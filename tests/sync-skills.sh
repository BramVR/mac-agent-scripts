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

new_case
make_skill "$agent_skills" shared
run_sync >/dev/null

assert_link "$agents_root/shared" "$(canonical "$agent_skills/shared")"
repeat_output=$(run_sync)
[ "$repeat_output" = 'skills mirror up to date (1 skills)' ] || fail "unexpected repeat output: $repeat_output"

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
  assert_contains "$dry_run_output" "pruned stale link stale-$label -> $managed_target"
done
assert_contains "$dry_run_output" '(dry run; no changes written)'

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
