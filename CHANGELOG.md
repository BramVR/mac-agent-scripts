---
summary: Timeline of guardrail helper changes mirrored from Sweetistics and related repos.
---

# Changelog

## 2026-07-22 — Remove Legacy Maintainer Loop
- Removed the legacy current-repository `bram-maintainer-loop` skill and project-loop prompt; maintainer orchestration now routes only through `bram-maintainer-loop-v2`.

## 2026-07-22 — Codex First Refresh
- Refreshed `codex-first` from ten upstream commits: hard gate with autoreview exception, widened routing (diagnose-then-fix, exploratory subagents, git mechanics/PR landing), `gpt-5.6-sol` + high effort pinning, ChatGPT-app PATH recipe, harness-tracked background launches, and the liveness watchdog with explicit-id resume.
- Bram-local deviations: never fast mode (flag dropped from every invocation), maintainer pointer stays `$bram-maintainer-loop-v2`, loopback-only proxy gate without upstream's personal router host, and the huge-context preflight points at the flat skill mirror.

## 2026-07-22 — Codex Huge Context
- Adopted upstream `codex-huge-context` skill for the Codex 1M-token direct OpenAI Responses API route: safe 922k input window, 820k total-scope compaction, Keychain-only credential delivery, and the secret-safe `preflight.rb` check.
- Scrubbed upstream personal assumptions: no hardcoded `/Users/steipete` paths, no named 1Password vault item, no Mac-fleet rollout section; credential handling routes through `$one-password`.
- Preflight path targets the flat skill mirror (`~/.codex/skills/codex-huge-context/...`), not upstream's whole-root `~/.codex/skills/agent-scripts/` symlink layout.
- Added a Bram-local hard rule: never fast mode on the huge-context route, overriding the `$codex-first` house default.

## 2026-07-22 — Skill Mirror Sync
- Added `scripts/sync-skills`, adapted from upstream, so Claude Code and Codex share one canonical per-skill mirror across agent-scripts, optional manager skills, and codex-local extras.
- Kept Bram's documented flat per-skill layout for both roots instead of upstream's whole-root Codex symlink, added `--dry-run`/`--no-instructions` and path overrides, and canonicalized targets so repo-owned skills resolve to their own repo.
- First run pruned nine broken links from a removed skill experiment and published ~20 skills that were present in `skills/` but missing from `~/.claude/skills`.

## 2026-07-14 — Craft Prompt
- Added a live-guidance-first interview-style GPT-5.6 prompt-crafting skill plus `/prompts:craft-prompt` compatibility command, with bundled offline guidance as fallback.

## 2026-07-13 — Bram Maintainer Loop v2
- Added a Peter-style cross-repository maintainer loop for `BramVR`, with one persistent Codex app task per repository, a 30-repository concurrency target, autonomous dependency upgrades, serialized public mutations, live proof, autoreview, and verified release proposals.

## 2026-07-01 — Current-Repo Maintainer Loop
- Reworked `bram-maintainer-loop` from latest upstream orchestration mechanics for one root loop and heartbeat per canonical repository, fresh issue/PR workers, autonomous supported land/close, TDD/PRD routing, Claude Opus extra review, public artifact confidentiality, dependency freshness, and release-specific blockers.

## 2026-06-23 — Auto Review Loop Gate
- Added a `claude-opus` autoreview preset for standalone Claude Opus 4.8 review and updated the maintainer loop to run default Codex review plus the Claude Opus review as separate closeout gates.

## 2026-06-13 — Auto Review Skill
- Added Bram-owned `autoreview` skill from upstream structured review workflow, keeping Codex as default and preserving local CLI model defaults unless explicitly overridden.
- Removed legacy `codex-review` skill so review routing uses `autoreview`.

## 2026-06-13 — Bram Maintainer Loop
- Added `bram-maintainer-loop` from upstream maintainer orchestration mechanics, adapted to Bram's flagged repos, authorization boundaries, TDD/issue/PRD skills, and autoreview gate.
- Upgraded GitHub triage with upstream URL-first queue cards, autonomous-candidate classification, owner-comment authority, and factual contributor activity helper.
- Matched upstream empty-queue release behavior so idle maintained repos become patch/minor release candidates after release gates pass.
- Added upstream-style dependency freshness handling for idle repositories, including package health, prerelease avoidance, compatibility tests, live proof, autoreview, public artifact audit, and CI.
- Added upstream-style heartbeat automation guidance for continuous loop monitoring.
- Added upstream-style public model identifier audit detail to the broader public artifact confidentiality gate.
- Matched upstream decision-ready PR assumptions: implement issues on branches, create PRs, push final candidates, and ask Bram only after mergeable proof is ready.
- Switched maintainer-loop state guidance from one global markdown file to one dated markdown ledger per loop.

## 2026-05-31 — GitHub Offline Fallback
- Added a live-first `gh` wrapper plus GitHub offline prewarm helper so normal reads warm gitcrawl and fall back to cached data only during outages, rate limits, or explicit offline requests.
- Skipped `openai/codex` by default in GitHub offline prewarm and added include/skip filters to avoid spending cache budget on repos Bram does not maintain.

## 2026-05-30 — Bram Agent Setup Refresh
- Added Bram-focused setup docs, smoke CI, active skill links, Chrome network capture, safer 1Password guidance, and paired `wacli` routing for WhatsApp linked-device work.
- Removed unused Claw/OpenClaw/Peter-specific skills and broken local symlinks from the Bram setup.

## 2026-05-25 — To PRD Skill
- Added `to-prd` as a Codex-linked skill for turning current context into a GitHub issue-ready PRD.

## 2026-05-14 — Codex Review Finding Detection
- Updated `codex-review` to capture review output, report elapsed time, fail on reported P0-P3 findings, and treat empty review output as non-clean.

## 2026-05-14 — Codex Review Full Access
- Added `codex-review --full-access` for nested review runs that need localhost bind/listen tests without sandbox noise.

## 2026-05-14 — GitHub Search Shim Guidance
- Added AGENTS guidance to prefer shimmed `gh` / `gitcrawl gh` for broad reads and avoid raw Search API POST mistakes.

## 2026-05-14 — Codex Review Base Caveat
- Documented that `codex review --base` must not include an inline prompt; use a separate follow-up pass for custom instructions.
- Clarified that committed or PR branch review must use branch/base mode, not `--uncommitted` / local mode.

## 2026-05-14 — Codex Review Loop Guidance
- Clarified that `codex-review` should iterate until no accepted findings remain and document intentional rejections with useful inline comments when warranted.

## 2026-05-14 — README Skills Overview
- Rewrote the README around agent instructions, skills, helper scripts, and sync expectations; removed stale copied-origin notes.

## 2026-05-14 — Codex Review Skill
- Added a `codex-review` skill and helper for closeout reviews, with stdout-only default output and subagent filtering guidance for noisy review output.

## 2026-05-13 — Checkout Discipline
- Added CLI checkout/worktree guardrails: stay in repo cwd by default, never create worktrees unless asked, and treat sibling checkouts under `~/Projects` as user-managed.

## 2026-05-13 — Skill Metadata Guardrails
- Added generic skill-description guidance and quieter browser recovery notes to reduce noisy auth prompts and token-heavy skill metadata.

## 2025-12-22 — Remove Custom rm Shim
- Dropped `bin/rm` and `scripts/trash.ts`; rely on the system `trash` command for recoverable deletes.

## 2025-12-17 — Remove Runner; Keep Guardrails
- Removed the `runner` wrapper and `scripts/runner.ts` now that modern Codex sessions handle long-running/background work directly.
- Kept the safety-critical bits as standalone shims: `bin/rm` (moves deletes to Trash via `scripts/trash.ts`).
- Dropped the `find -delete` interception and the `bin/sleep` shim.

## 2025-12-02 — Release Preflight Helpers
- Added shared release helpers in `release/sparkle_lib.sh`: clean working-tree check, Sparkle key probe, changelog finalization/notes extraction, and appcast monotonicity guard for version/build.
- Documented the helper functions in `docs/RELEASING-MAC.md` so Trimmy/CodexBar-style release scripts can reuse them.

## 2025-11-18 — Console Log Capture
- Added `console` command to `scripts/browser-tools.ts` for capturing and monitoring Chrome DevTools console output with real-time formatting, type filtering (log, error, warn, etc.), continuous follow mode, and configurable timeouts with automatic object serialization.

## 2025-11-22 — Search & Content Extraction
- Added `search` and `content` commands to `scripts/browser-tools.ts` for Google SERP scraping with optional readable markdown extraction and single-URL readability output, leveraging the existing DevTools-connected Chrome instance.
- `eval` now supports `--pretty-print` to inspect complex objects with indentation and colors.

## 2025-11-15 — Chrome Browser Tools
- Added `scripts/browser-tools.ts`, a DevTools-ready Chrome helper copied from the Oracle repo so agents can inspect, screenshot, and terminate sessions without dragging in the full CLI. The workflow is inspired by Mario Zechner’s [“What if you don’t need MCP?”](https://mariozechner.at/posts/2025-11-02-what-if-you-dont-need-mcp/).
- Documented the new helper in the README so downstream repos know how to run `pnpm tsx scripts/browser-tools.ts --help`.

## 2025-11-16 — Browser Tools Pipe Detection
- Updated `scripts/browser-tools.ts` to enumerate and kill Chrome instances started with `--remote-debugging-pipe` (the default for Peekaboo/Tachikoma) in addition to the classic `--remote-debugging-port`. List/kill now show “debugging pipe” when no port exists and still fetch tab metadata when it does.
- README now notes the optional `NODE_PATH=$(npm root -g)` trick so the helper can run from bare copies of the repo without a local `package.json`.

## 2025-11-14 — Compact Runner Summaries
- The runner's completion log now defaults to a compact `exit <code> in <time>` format so long commands don't repeat the entire input line.
- Added the `RUNNER_SUMMARY_STYLE` env var with `compact` (default), `minimal`, and `verbose` options so agents can pick how much detail they want without editing the script.
- Timeout heuristics now understand both `pnpm` and `bun` invocations automatically, so long-running Bun scripts/tests get the same guardrails without repo-specific patches.
- `sleep` invocations longer than 30 seconds are clamped to the 30s ceiling instead of erroring, which keeps wait hacks working while still honoring the AGENTS.MD limit.

## 2025-11-08 — Sleep Guardrail & Git Shim Refresh
- Runner now rejects any `sleep` argument longer than 30 seconds, mirroring the AGENTS rule and preventing long blocking waits.
- Added `bin/sleep` so plain `sleep` calls automatically route through the runner and inherit the enforcement without extra flags.
- Simplified `bin/git` to delegate directly to the runner + system git, eliminating the bespoke policy checker while keeping consent gates identical.

## 2025-11-08 — Guardrail Sync & Docs Hardening
- Synced guardrail helpers with Sweetistics so downstream repos share the same runner, docs-list helper, and supporting scripts.
- Expanded README guidance around runner usage, portability, and multi-repo sync expectations.
- Added committer lock cleanup, tightened path ignores, and refreshed misc. helper utilities (e.g., `toArray`) to reduce drift across repos.

## 2025-11-08 — Initial Toolkit Import
- Established the repo with the Sweetistics guardrail toolkit (runner, git policy enforcement, docs-list helper, etc.).
- Ported documentation from the main product repo so other projects inherit the identical safety rails and onboarding notes.
