#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "$0")/.." && pwd -P)
suite_root=$(mktemp -d "${TMPDIR:-/tmp}/sync-skills.XXXXXX")
suite_root=$(cd "$suite_root" && pwd -P)
trap 'rm -rf "$suite_root"' EXIT
case_index=0

fail() {
  printf '%s\n' "$*" >&2
  exit 1
}

new_case() {
  case_index=$((case_index + 1))
  case_root="$suite_root/$case_index"
  home="$case_root/home"
  agent_scripts="$case_root/agent-scripts"
  agent_skills="$agent_scripts/skills"
  manager_skills="$case_root/manager/skills"
  agents_root="$home/.agents/skills"
  state_file="$home/.agents/.sync-skills-v1.tsv"
  claude_root="$home/.claude/skills"
  codex_root="$home/.codex/skills"
  mkdir -p "$home" "$agent_skills" "$manager_skills"
}

make_skill() {
  mkdir -p "$1/$2"
  printf '%s\n' '---' "name: $2" '---' > "$1/$2/SKILL.md"
}

link_skill() {
  make_skill "$1" "$3"
  mkdir -p "$2"
  ln -s "$1/$3" "$2/$3"
}

canonical() {
  (cd "$1" 2>/dev/null && pwd -P)
}

file_inode() {
  if [ "$(uname -s)" = Darwin ]; then
    stat -f '%i' "$1"
  else
    stat -c '%i' "$1"
  fi
}

file_mode() {
  if [ "$(uname -s)" = Darwin ]; then
    stat -f '%Lp' "$1"
  else
    stat -c '%a' "$1"
  fi
}

run_sync() {
  HOME="$home" \
    AGENT_SCRIPTS_DIR="$agent_scripts" \
    MANAGER_SKILLS_DIR="$manager_skills" \
    "$repo_root/scripts/sync-skills" --no-instructions "$@"
}

assert_link() {
  local path=$1 expected=$2 actual
  actual=$(readlink "$path" 2>/dev/null || true)
  [ "$actual" = "$expected" ] || fail "expected $path -> $expected, got ${actual:-missing}"
}

assert_absent() {
  [ ! -e "$1" ] && [ ! -L "$1" ] || fail "expected $1 to be absent"
}

assert_contains() {
  case $1 in
    *"$2"*) ;;
    *) fail "expected output to contain: $2" ;;
  esac
}

assert_not_contains() {
  case $1 in
    *"$2"*) fail "expected output not to contain: $2" ;;
  esac
}

assert_file_text() {
  local actual
  actual=$(cat "$1")
  [ "$actual" = "$2" ] || fail "unexpected contents in $1: $actual"
}

for mode in normal dry-run; do
  new_case
  backing_root="$case_root/agents-backing"
  mkdir -p "$backing_root"
  printf 'keep sentinel\n' > "$backing_root/sentinel"
  make_skill "$backing_root" healthy
  ln -s "$case_root/missing" "$backing_root/broken"
  mkdir -p "$home/.agents"
  ln -s "$backing_root" "$agents_root"
  make_skill "$agent_skills" mirrored

  set +e
  if [ "$mode" = dry-run ]; then
    root_symlink_output=$(run_sync --dry-run 2>&1)
  else
    root_symlink_output=$(run_sync 2>&1)
  fi
  root_symlink_status=$?
  set -e

  [ "$root_symlink_status" -ne 0 ] || fail "expected $mode root symlink run to fail"
  [ "$root_symlink_output" = "WARN: $agents_root must be a real directory, not a symlink" ] || fail "unexpected $mode root symlink output: $root_symlink_output"
  assert_link "$agents_root" "$backing_root"
  [ "$(cat "$backing_root/sentinel")" = 'keep sentinel' ] || fail "changed $mode sentinel"
  [ -f "$backing_root/healthy/SKILL.md" ] || fail "changed $mode healthy skill"
  assert_link "$backing_root/broken" "$case_root/missing"
  assert_absent "$backing_root/mirrored"
done

for state_kind in malformed symlink; do
  for mode in normal dry-run; do
    new_case
    backing_root="$case_root/claude-backing"
    mkdir -p "$backing_root" "$codex_root" "$home/.agents" "$home/.claude"
    printf 'keep claude\n' > "$backing_root/sentinel"
    printf 'keep codex\n' > "$codex_root/sentinel"
    ln -s "$backing_root" "$claude_root"
    if [ "$state_kind" = malformed ]; then
      printf 'wrong-version\n' > "$state_file"
    else
      printf 'sync-skills-v1\n' > "$case_root/state-target"
      ln -s "$case_root/state-target" "$state_file"
    fi

    set +e
    if [ "$mode" = dry-run ]; then
      state_output=$(run_sync --dry-run 2>&1)
    else
      state_output=$(run_sync 2>&1)
    fi
    state_status=$?
    set -e

    [ "$state_status" -ne 0 ] || fail "expected $mode with $state_kind state to fail"
    assert_link "$claude_root" "$backing_root"
    [ "$(cat "$backing_root/sentinel")" = 'keep claude' ] || fail "changed Claude backing for $mode with $state_kind state"
    [ "$(cat "$codex_root/sentinel")" = 'keep codex' ] || fail "changed Codex root for $mode with $state_kind state"
    case $state_kind in
      malformed) assert_contains "$state_output" "invalid ownership state $state_file" ;;
      symlink) assert_contains "$state_output" "$state_file must be a regular file" ;;
    esac
  done
done

new_case
make_skill "$agent_skills" shared
run_sync >/dev/null

assert_link "$agents_root/shared" "$(canonical "$agent_skills/shared")"
[ "$(file_mode "$state_file")" = 600 ] || fail 'expected ownership state mode 600'
state_inode=$(file_inode "$state_file")
repeat_output=$(run_sync)
[ "$repeat_output" = 'skills mirror up to date (1 skills)' ] || fail "unexpected repeat output: $repeat_output"
[ "$(file_inode "$state_file")" = "$state_inode" ] || fail 'rewrote unchanged ownership state'

new_case
make_skill "$codex_root" quiet-real-source
quiet_real_output=$(run_sync 2>&1)
assert_not_contains "$quiet_real_output" "$codex_root/quiet-real-source is a real file/dir"
assert_link "$agents_root/quiet-real-source" "$(canonical "$codex_root/quiet-real-source")"
assert_link "$claude_root/quiet-real-source" "$(canonical "$codex_root/quiet-real-source")"

new_case
link_skill "$case_root/local-sources/codex" "$codex_root" codex-deleted
codex_deleted=$(canonical "$case_root/local-sources/codex/codex-deleted")
run_sync >/dev/null

assert_link "$agents_root/codex-deleted" "$codex_deleted"
assert_link "$claude_root/codex-deleted" "$codex_deleted"
[ -f "$state_file" ] || fail "expected ownership state at $state_file"
assert_file_text "$state_file" "sync-skills-v1
agents	codex-deleted	$codex_deleted
claude	codex-deleted	$codex_deleted"
rm "$codex_root/codex-deleted"
run_sync >/dev/null
for root in "$agents_root" "$claude_root" "$codex_root"; do
  assert_absent "$root/codex-deleted"
done
[ -f "$case_root/local-sources/codex/codex-deleted/SKILL.md" ] || fail 'removed external Codex target'
repeat_output=$(run_sync)
[ "$repeat_output" = 'skills mirror up to date (0 skills)' ] || fail "unexpected deletion repeat output: $repeat_output"

new_case
link_skill "$case_root/local-sources/claude" "$claude_root" claude-deleted
claude_deleted=$(canonical "$case_root/local-sources/claude/claude-deleted")
run_sync >/dev/null

assert_link "$agents_root/claude-deleted" "$claude_deleted"
assert_link "$codex_root/claude-deleted" "$claude_deleted"
rm "$claude_root/claude-deleted"
run_sync >/dev/null
for root in "$agents_root" "$claude_root" "$codex_root"; do
  assert_absent "$root/claude-deleted"
done
[ -f "$case_root/local-sources/claude/claude-deleted/SKILL.md" ] || fail 'removed external Claude target'

new_case
make_skill "$case_root/ambiguous" ambiguous
ambiguous=$(canonical "$case_root/ambiguous/ambiguous")
mkdir -p "$codex_root" "$claude_root"
ln -s "$ambiguous" "$codex_root/ambiguous"
ln -s "$ambiguous" "$claude_root/ambiguous"
run_sync >/dev/null

assert_file_text "$state_file" "sync-skills-v1
agents	ambiguous	$ambiguous"
rm "$codex_root/ambiguous"
run_sync >/dev/null
assert_link "$claude_root/ambiguous" "$ambiguous"
assert_link "$codex_root/ambiguous" "$ambiguous"
assert_link "$agents_root/ambiguous" "$ambiguous"

new_case
link_skill "$case_root/local-sources/codex" "$codex_root" relinquished
original=$(canonical "$case_root/local-sources/codex/relinquished")
run_sync >/dev/null
make_skill "$case_root/local-sources/replacement" relinquished
replacement=$(canonical "$case_root/local-sources/replacement/relinquished")
rm "$claude_root/relinquished" "$codex_root/relinquished"
ln -s "$replacement" "$claude_root/relinquished"
run_sync >/dev/null

assert_link "$claude_root/relinquished" "$replacement"
assert_link "$agents_root/relinquished" "$replacement"
assert_link "$codex_root/relinquished" "$replacement"
[ -f "$original/SKILL.md" ] || fail 'removed original relinquished target'
assert_not_contains "$(cat "$state_file")" "claude	relinquished"

new_case
link_skill "$case_root/local-sources/codex" "$codex_root" removal-crash
removal_crash=$(canonical "$case_root/local-sources/codex/removal-crash")
run_sync >/dev/null
rm "$agents_root/removal-crash"
run_sync >/dev/null

assert_link "$agents_root/removal-crash" "$removal_crash"
assert_link "$claude_root/removal-crash" "$removal_crash"
assert_link "$codex_root/removal-crash" "$removal_crash"

new_case
link_skill "$case_root/local-sources/codex" "$codex_root" manifest-crash
manifest_crash=$(canonical "$case_root/local-sources/codex/manifest-crash")
mkdir -p "$home/.agents"
printf 'sync-skills-v1\nagents\tmanifest-crash\t%s\n' "$manifest_crash" > "$state_file"
run_sync >/dev/null

assert_link "$agents_root/manifest-crash" "$manifest_crash"
assert_link "$claude_root/manifest-crash" "$manifest_crash"
rm "$codex_root/manifest-crash" "$agents_root/manifest-crash" "$claude_root/manifest-crash"
printf 'sync-skills-v1\nagents\tmanifest-crash\t%s\n' "$manifest_crash" > "$state_file"
run_sync >/dev/null
assert_file_text "$state_file" 'sync-skills-v1'
for root in "$agents_root" "$claude_root" "$codex_root"; do
  assert_absent "$root/manifest-crash"
done

new_case
make_skill "$agent_skills" foo
mkdir -p "$agents_root"
ln -s "$agent_skills/foo" "$case_root/intermediate-foo"
ln -s "$case_root/intermediate-foo" "$agents_root/foo"
run_sync >/dev/null

assert_link "$agents_root/foo" "$(canonical "$agent_skills/foo")"

new_case
make_skill "$claude_root" foo
run_sync >/dev/null
claude_foo=$(canonical "$claude_root/foo")
assert_link "$agents_root/foo" "$claude_foo"
assert_link "$codex_root/foo" "$claude_foo"

rm "$codex_root/foo"
make_skill "$codex_root" foo
codex_foo=$(canonical "$codex_root/foo")
run_sync >/dev/null 2>&1

assert_link "$agents_root/foo" "$codex_foo"
[ -d "$claude_root/foo" ] && [ ! -L "$claude_root/foo" ] || fail "expected real Claude skill at $claude_root/foo"
[ -d "$codex_root/foo" ] && [ ! -L "$codex_root/foo" ] || fail "expected real Codex skill at $codex_root/foo"
repeat_output=$(run_sync 2>&1)
assert_contains "$repeat_output" 'skills mirror up to date (1 skills)'
assert_link "$agents_root/foo" "$codex_foo"
[ -d "$claude_root/foo" ] && [ ! -L "$claude_root/foo" ] || fail "changed real Claude skill at $claude_root/foo"
[ -d "$codex_root/foo" ] && [ ! -L "$codex_root/foo" ] || fail "changed real Codex skill at $codex_root/foo"

new_case
make_skill "$agent_skills" agent-source
make_skill "$manager_skills" manager-source
link_skill "$case_root/local-sources/codex" "$codex_root" codex-source
link_skill "$case_root/local-sources/claude" "$claude_root" claude-source

make_skill "$agent_skills" priority-agent
make_skill "$manager_skills" priority-agent
link_skill "$case_root/local-sources/codex" "$codex_root" priority-agent
link_skill "$case_root/local-sources/claude" "$claude_root" priority-agent

make_skill "$manager_skills" priority-manager
link_skill "$case_root/local-sources/codex" "$codex_root" priority-manager
link_skill "$case_root/local-sources/claude" "$claude_root" priority-manager

link_skill "$case_root/local-sources/codex" "$codex_root" priority-codex
link_skill "$case_root/local-sources/claude" "$claude_root" priority-codex
link_skill "$case_root/local-sources/claude" "$claude_root" priority-claude

run_sync >/dev/null

expected_names=(agent-source manager-source codex-source claude-source priority-agent priority-manager priority-codex priority-claude)
expected_targets=(
  "$agent_skills/agent-source"
  "$manager_skills/manager-source"
  "$case_root/local-sources/codex/codex-source"
  "$case_root/local-sources/claude/claude-source"
  "$agent_skills/priority-agent"
  "$manager_skills/priority-manager"
  "$case_root/local-sources/codex/priority-codex"
  "$case_root/local-sources/claude/priority-claude"
)

for i in "${!expected_names[@]}"; do
  expected=$(canonical "${expected_targets[$i]}")
  for root in "$agents_root" "$claude_root" "$codex_root"; do
    assert_link "$root/${expected_names[$i]}" "$expected"
  done
done

new_case
link_skill "$case_root/foreign-agents" "$agents_root" agents-only
agents_only=$(canonical "$case_root/foreign-agents/agents-only")
run_sync >/dev/null

assert_link "$agents_root/agents-only" "$agents_only"
assert_absent "$codex_root/agents-only"
assert_absent "$claude_root/agents-only"

new_case
mkdir -p "$agents_root/foreign-target" "$claude_root"
ln -s "$agents_root/foreign-target" "$claude_root/agents-target"
run_sync >/dev/null

assert_link "$claude_root/agents-target" "$agents_root/foreign-target"
assert_absent "$codex_root/agents-target"

new_case
mkdir -p "$agents_root" "$codex_root/prefix-target/child" "$claude_root/prefix-target/child"
make_skill "$agent_skills" agent-prefix-target
make_skill "$manager_skills" manager-prefix-target
prefix_targets=(
  "$agent_skills/agent-prefix-target"
  "$manager_skills/manager-prefix-target"
  "$codex_root/prefix-target/child"
  "$claude_root/prefix-target/child"
)
for prefix_index in "${!prefix_targets[@]}"; do
  ln -s "${prefix_targets[$prefix_index]}" "$agents_root/foreign-prefix-$prefix_index"
done
run_sync >/dev/null

for prefix_index in "${!prefix_targets[@]}"; do
  assert_link "$agents_root/foreign-prefix-$prefix_index" "${prefix_targets[$prefix_index]}"
done

new_case
make_skill "$claude_root" foo
run_sync >/dev/null
claude_foo=$(canonical "$claude_root/foo")
rm "$codex_root/foo"
make_skill "$codex_root" foo
codex_foo=$(canonical "$codex_root/foo")

dry_run_output=$(run_sync --dry-run 2>&1)
assert_link "$agents_root/foo" "$claude_foo"
[ -d "$claude_root/foo" ] && [ ! -L "$claude_root/foo" ] || fail "expected real Claude skill at $claude_root/foo"
[ -d "$codex_root/foo" ] && [ ! -L "$codex_root/foo" ] || fail "expected real Codex skill at $codex_root/foo"
assert_contains "$dry_run_output" "link $agents_root/foo -> $codex_foo"
assert_contains "$dry_run_output" '(dry run; no changes written)'

new_case
make_skill "$agent_skills" dry-run-source
dry_run_output=$(run_sync --dry-run)
for root in "$agents_root" "$claude_root" "$codex_root"; do
  assert_absent "$root"
  assert_contains "$dry_run_output" "link $root/dry-run-source -> $(canonical "$agent_skills/dry-run-source")"
done
assert_contains "$dry_run_output" '(dry run; no changes written)'

new_case
mkdir -p "$agents_root" "$claude_root" "$codex_root"
mkdir -p "$agent_skills/managed-target"
managed_target=$(canonical "$agent_skills/managed-target")
for root in "$agents_root" "$claude_root" "$codex_root"; do
  label=$(basename "$(dirname "$root")")
  ln -s "$case_root/missing-$label" "$root/broken-$label"
  ln -s "$managed_target" "$root/stale-$label"
done

dry_run_output=$(run_sync --dry-run)
for root in "$agents_root" "$claude_root" "$codex_root"; do
  label=$(basename "$(dirname "$root")")
  assert_link "$root/broken-$label" "$case_root/missing-$label"
  assert_link "$root/stale-$label" "$managed_target"
  assert_contains "$dry_run_output" "pruned broken link broken-$label -> $case_root/missing-$label"
  assert_not_contains "$dry_run_output" "pruned stale link stale-$label -> $managed_target"
done
assert_contains "$dry_run_output" '(dry run; no changes written)'

new_case
make_skill "$agent_skills" initial
run_sync >/dev/null
state_before=$(cat "$state_file")
state_inode_before=$(file_inode "$state_file")
make_skill "$agent_skills" dry-state

dry_run_output=$(run_sync --dry-run)
assert_absent "$agents_root/dry-state"
assert_absent "$claude_root/dry-state"
assert_absent "$codex_root/dry-state"
assert_file_text "$state_file" "$state_before"
[ "$(file_inode "$state_file")" = "$state_inode_before" ] || fail 'dry-run replaced ownership state'
[ -z "$(find "$home/.agents" -name '.sync-skills-v1.tsv.tmp.*' -print)" ] || fail 'dry-run created a state temporary file'
assert_contains "$dry_run_output" "update ownership state $state_file"

new_case
make_skill "$agent_skills" file-collision
make_skill "$agent_skills" directory-collision
make_skill "$agent_skills" retarget
mkdir -p "$agents_root" "$claude_root" "$codex_root"
for root in "$agents_root" "$claude_root" "$codex_root"; do
  label=$(basename "$(dirname "$root")")
  printf 'keep %s file\n' "$label" > "$root/file-collision"
  mkdir -p "$root/directory-collision"
  printf 'keep %s directory\n' "$label" > "$root/directory-collision/marker"
  link_skill "$case_root/wrong-$label" "$root" retarget
  mkdir -p "$case_root/foreign-$label"
  ln -s "$case_root/foreign-$label" "$root/foreign-$label"
done

run_sync >/dev/null 2>&1
retarget_expected=$(canonical "$agent_skills/retarget")
for root in "$agents_root" "$claude_root" "$codex_root"; do
  label=$(basename "$(dirname "$root")")
  [ ! -L "$root/file-collision" ] || fail "expected real file at $root/file-collision"
  [ "$(cat "$root/file-collision")" = "keep $label file" ] || fail "changed $root/file-collision"
  [ ! -L "$root/directory-collision" ] || fail "expected real directory at $root/directory-collision"
  [ "$(cat "$root/directory-collision/marker")" = "keep $label directory" ] || fail "changed $root/directory-collision"
  assert_link "$root/retarget" "$retarget_expected"
  assert_link "$root/foreign-$label" "$case_root/foreign-$label"
done

new_case
make_skill "$agent_skills" removed-agent
make_skill "$manager_skills" removed-manager
run_sync >/dev/null
rm "$agent_skills/removed-agent/SKILL.md" "$manager_skills/removed-manager/SKILL.md"
for root in "$agents_root" "$claude_root" "$codex_root"; do
  label=$(basename "$(dirname "$root")")
  ln -s "$case_root/missing-$label" "$root/broken-$label"
done

prune_output=$(run_sync)
for root in "$agents_root" "$claude_root" "$codex_root"; do
  label=$(basename "$(dirname "$root")")
  assert_absent "$root/removed-agent"
  assert_absent "$root/removed-manager"
  assert_absent "$root/broken-$label"
  assert_contains "$prune_output" "pruned broken link broken-$label -> $case_root/missing-$label"
done
assert_contains "$prune_output" "pruned stale link removed-agent -> $(canonical "$agent_skills/removed-agent")"
assert_contains "$prune_output" "pruned stale link removed-manager -> $(canonical "$manager_skills/removed-manager")"

printf 'sync-skills tests passed\n'
