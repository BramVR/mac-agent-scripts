---
name: github-cache-hygiene
description: "GitHub live-first fallback: gh wrapper, gitcrawl, xcache, mirrors, rate limits."
---

# GitHub Cache Hygiene

Goal: keep `gh` live-first while preserving automatic offline/cache fallback for GitHub outages, rate limits, and old-thread research.

## Default Path

Use `gh` normally. Bram's `gh` should be `scripts/gh-live-first` on PATH before Homebrew `gh`; it calls real `/opt/homebrew/bin/gh` first, then best-effort warms gitcrawl for cacheable reads, and falls back to `gitcrawl gh` only when real GitHub fails with outage/rate-limit symptoms.

Wrapper controls:

```bash
GH_OFFLINE=1 gh pr view 123 -R owner/repo --json number,title,url
GH_WARM=0 gh pr view 123 -R owner/repo --json number,title,url
GH_WARM_SYNC=1 gh pr view 123 -R owner/repo --json number,title,url
gh --live pr view 123 -R owner/repo --json number,title,url
```

Use `GH_OFFLINE=1 gh ...` or `gitcrawl gh ...` when the user explicitly asks for cached/offline data. Sync exact rows while GitHub is available if they may be needed offline later:

```bash
/Users/bram/Projects/agent-scripts/scripts/github-offline-prewarm
gitcrawl sync owner/repo --numbers 123 --with pr-details
GH_OFFLINE=1 gh search issues "<terms>" -R owner/repo --state open --json number,title,state,url,updatedAt,labels,author
GH_OFFLINE=1 gh search prs "<terms>" -R owner/repo --state open --json number,title,state,url,updatedAt,isDraft,author
GH_OFFLINE=1 gh issue list -R owner/repo --state open --author user --assignee user --label bug --json number,title,url
GH_OFFLINE=1 gh pr list -R owner/repo --state open --author user --label dependencies --json number,title,url
GH_OFFLINE=1 gh issue view 123 -R owner/repo --json number,title,state,body,comments,labels,url
GH_OFFLINE=1 gh pr view 123 -R owner/repo --json number,title,state,body,comments,labels,files,commits,statusCheckRollup,url
GH_OFFLINE=1 gh pr diff 123 -R owner/repo --patch
gitcrawl gh --cached pr status 123 -R owner/repo --compact
```

Use exact refs and narrow fields. Avoid broad loops like one `gh issue view` per result when a single `gh search` or `gh issue list --json ...` can answer the first-pass question.

For CI, avoid tight `gh run list` / `gh run view` polling loops. After a push or workflow dispatch, identify one exact run, then poll it with backoff. Fetch full logs only for failed jobs or when the user explicitly asks for logs. The wrapper keeps `gh run`, `gh workflow`, `gh pr checks`, and `gh release` live-only; cached CI/release reads require explicit `gitcrawl gh --cached ...` and are only fallback/history.

## Freshness

Local answers are good for GitHub outages, duplicate search, old thread review, author/label triage, and "is there likely already an issue/PR?" checks.

The wrapper stays live-only for:

- writing, commenting, closing, merging, rerunning, or editing
- checking final current state before a maintainer action
- verifying CI status after a push
- the local result is missing or obviously stale
- the user asks for latest/live state

For PR review, normal successful cacheable `gh` reads should warm gitcrawl in the background. Hydrate exact PR details once with `gitcrawl sync owner/repo --numbers <n> --with pr-details` when offline fallback must be reliable before travel/outage. The fallback shim can auto-hydrate one exact PR on miss while GitHub is reachable, using `GITHUB_TOKEN` or `gh auth token`; explicit hydration makes intent and cost clearer.

Run `/Users/bram/Projects/agent-scripts/scripts/github-offline-prewarm` while GitHub is healthy to sync open issues/PRs with PR details for local GitHub remotes under `~/Projects`. Tune scope with:

```bash
GITHUB_OFFLINE_PREWARM_LIMIT=25 /Users/bram/Projects/agent-scripts/scripts/github-offline-prewarm ~/Projects
GITHUB_OFFLINE_PREWARM_MODE=all /Users/bram/Projects/agent-scripts/scripts/github-offline-prewarm ~/Projects/oss
GITHUB_OFFLINE_PREWARM_SKIP=openai/codex,owner/large-repo /Users/bram/Projects/agent-scripts/scripts/github-offline-prewarm ~/Projects
GITHUB_OFFLINE_PREWARM_INCLUDE='BramVR/*,openclaw/*' /Users/bram/Projects/agent-scripts/scripts/github-offline-prewarm ~/Projects
```

After a write, do one targeted readback, not a broad rescan.

## XCache

Inspect cache behavior when rate limits are suspected:

```bash
gitcrawl gh xcache stats
gitcrawl gh xcache keys
gitcrawl gh xcache gc
```

Read `backend_misses_by_command` and `backend_misses_by_route` in `gitcrawl gh xcache stats --json` before adding new live GitHub loops. Those maps show which command shapes are still escaping the cache.

Use `gitcrawl gh xcache flush` only when a stale cached fallback read is misleading a decision.

For local-only proof, temporarily make the backend unavailable for a single command:

```bash
GITCRAWL_GH_PATH=/tmp/no-real-gh gitcrawl gh search issues "<terms>" -R owner/repo --json number,title,url
```

## Agent Etiquette

Batch questions by repo and state. Reuse data already printed in the session. Back off CI polling; inspect logs only for failing runs or the exact run under review. Do not install raw `gitcrawl` as `gh`; `gh` should point to the live-first wrapper, and the wrapper should point at real Homebrew `gh`.
