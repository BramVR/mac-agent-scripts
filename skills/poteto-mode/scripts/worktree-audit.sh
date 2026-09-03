#!/usr/bin/env bash
# Read-only worktree prune audit. Classifies every git worktree by size, merge
# state, uncommitted work, remote/PR state, and the most recent chat that
# operated in it. Emits a table sorted by size with a suggested bucket. Never
# deletes anything; deletion stays a human-gated step in the playbook.
#
# Usage: worktree-audit.sh [repo-path]   (defaults to the current repo)
set -u

repo="${1:-$(git rev-parse --show-toplevel 2>/dev/null)}"
[ -z "$repo" ] && { echo "not in a git repo; pass a repo path" >&2; exit 1; }
cd "$repo" || exit 1

# Main worktree is the first entry; everything else is a candidate. NUL-delimited
# porcelain preserves paths containing spaces.
worktrees=()
while IFS= read -r -d '' field; do
	case "$field" in
		"worktree "*) worktrees+=("${field#worktree }") ;;
	esac
done < <(git worktree list --porcelain -z)
[ "${#worktrees[@]}" -eq 0 ] && { echo "git reported no worktrees" >&2; exit 1; }
main_wt="${worktrees[0]}"

# The remote default branch drives the merge check. This audit never fetches.
trunk_ref=$(git symbolic-ref --quiet refs/remotes/origin/HEAD 2>/dev/null || echo "")
if [ -z "$trunk_ref" ] || ! git show-ref --verify --quiet "$trunk_ref"; then
	trunk_ref=""
	echo "warn: origin/HEAD is unavailable; set it and fetch before trusting the merged column" >&2
fi

# PR state by branch, fetched once. Empty if gh is unavailable.
prs=$(mktemp)
if gh pr list --state all --limit 1000 \
	--json number,state,headRefName > "$prs" 2>/dev/null; then
	pr_snapshot_complete=yes
	[ "$(jq 'length' "$prs" 2>/dev/null || echo 1000)" -ge 1000 ] && pr_snapshot_complete=no
else
	echo "[]" > "$prs"
	pr_snapshot_complete=no
	echo "warn: GitHub PR state is unavailable; unmatched branches are UNKNOWN" >&2
fi

# Exact current-thread rollout. Resolve by thread id from filenames only; never
# read unrelated Codex sessions. CODEX_CURRENT_ROLLOUT remains an explicit
# override for callers outside a Codex shell.
transcript="${CODEX_CURRENT_ROLLOUT:-}"
if [ -z "$transcript" ] && [ -n "${CODEX_THREAD_ID:-}" ]; then
	session_root="${CODEX_HOME:-$HOME/.codex}/sessions"
	transcript=$(find "$session_root" -type f -name "*${CODEX_THREAD_ID}.jsonl" -print -quit 2>/dev/null)
fi
now=$(date +%s)

printf "SIZE\tAGE\tMERGED\tDIRTY\tREMOTE\tPR\tLAST_CHAT\tBUCKET\tWORKTREE\n"

for wt in "${worktrees[@]}"; do
	[ "$wt" = "$main_wt" ] && continue

	size=$(du -sh "$wt" 2>/dev/null | awk '{print $1}')
	head=$(git -C "$wt" rev-parse HEAD 2>/dev/null)
	head_ts=$(git -C "$wt" log -1 --format='%ct' HEAD 2>/dev/null || echo 0)
	age=$([ "$head_ts" -gt 0 ] 2>/dev/null && echo "$(( (now - head_ts) / 86400 ))d" || echo "?")

	# Squash-merged branches are not ancestors of main, so PR state is the
	# real signal; merge-base only catches fast-forward/rebase merges.
	if [ -z "$trunk_ref" ]; then merged=UNKNOWN
	elif git merge-base --is-ancestor "$head" "$trunk_ref" 2>/dev/null; then merged=YES
	else merged=no; fi

	# Distinguish real WIP (tracked edits) from disposable untracked scratch.
	if ! porcelain=$(git -C "$wt" status --porcelain 2>/dev/null); then dirty=UNKNOWN
	elif [ -z "$porcelain" ]; then dirty=clean
	elif printf '%s\n' "$porcelain" | grep -qv '^??'; then
		dirty="wip:$(printf '%s\n' "$porcelain" | grep -cv '^??')"
	else dirty="scratch:$(printf '%s\n' "$porcelain" | grep -c '^??')"; fi

	branch=$(git -C "$wt" symbolic-ref --quiet --short HEAD 2>/dev/null || echo "")
	if [ -z "$branch" ]; then remote=detached
	elif git -C "$wt" show-ref --verify --quiet "refs/remotes/origin/$branch"; then
		ahead=$(git -C "$wt" rev-list --count "origin/$branch..HEAD" 2>/dev/null || echo 0)
		behind=$(git -C "$wt" rev-list --count "HEAD..origin/$branch" 2>/dev/null || echo 0)
		if [ "$ahead" -eq 0 ] && [ "$behind" -eq 0 ]; then remote=pushed
		elif [ "$ahead" -gt 0 ] && [ "$behind" -eq 0 ]; then remote="ahead$ahead"
		elif [ "$ahead" -eq 0 ] && [ "$behind" -gt 0 ]; then remote="behind$behind"
		else remote="diverged+a${ahead}-b${behind}"; fi
	else remote=no-remote; fi

	pr=$([ -n "$branch" ] && jq -r --arg b "$branch" \
		'.[] | select(.headRefName==$b) | "#\(.number)/\(.state)"' "$prs" 2>/dev/null | head -1)
	if [ -z "$pr" ]; then
		[ "$pr_snapshot_complete" = yes ] && pr="-" || pr="UNKNOWN"
	fi

	# Most recent chat whose transcript operated in this worktree. Match path
	# followed by "/" or a quote so glint-482 does not match glint-482-r37.
	last="-"; last_ts=0
	if [ -f "$transcript" ]; then
		if rg -q -F -e "${wt}/" -e "${wt}\"" "$transcript" 2>/dev/null; then
			last_ts=$(stat -f '%m' "$transcript" 2>/dev/null || echo 0)
			last=$(date -r "$last_ts" '+%Y-%m-%d' 2>/dev/null); fi
	fi
	recent=$([ "$last_ts" -gt 0 ] 2>/dev/null && [ $(( (now - last_ts) / 86400 )) -le 4 ] && echo yes || echo no)

	case "$dirty" in wip:*|UNKNOWN) bucket=hold-wip ;; *)
		case "$pr" in *OPEN*) bucket=hold-open-pr ;; *)
			if [ "$recent" = yes ]; then bucket=verify-current-thread
			elif [ "$merged" = YES ] || [ "$pr" != "-" ]; then bucket=verify-active-tasks
			else bucket=review; fi ;;
		esac ;;
	esac

	printf "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" \
		"$size" "$age" "$merged" "$dirty" "$remote" "$pr" "$last" "$bucket" "$wt"
done | sort -t$'\t' -k1,1 -rh

rm -f "$prs"
