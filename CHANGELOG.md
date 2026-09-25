---
summary: Timeline of guardrail helper changes mirrored from Sweetistics and related repos.
---

# Changelog

## 2026-09-25: PStack split into Codex and Claude halves
- Stopped mirroring the 57 Codex-tuned PStack skills listed in `skills/.codex-only` into `~/.claude/skills`; `sync-skills` prunes its own links there and keeps them for `~/.agents` and `~/.codex`. Claude Code now gets PStack from the `pstack` plugin in the new private [BramVR/claude-pstack](https://github.com/BramVR/claude-pstack) fork of `michael-denyer/pstack-claude`, with Codex-parity model roles (Fable judgment, Opus code, Sonnet scouts) and an opt-in routing hook.

## 2026-09-23: Opus design and review roles
- Use Opus 5.5 for Interrogate at xhigh and optional Claude Autoreview at high; add it to Arena’s cross-judge pool at high, with Claude CLI routing and a 2.1.280 minimum-version check.
- Replace Architect’s Astra low candidate with Opus 5.5 high through `claude -p`; retain GPT-6 Sol high, Fable 5.1 high, and the three-candidate requirement.

## 2026-09-22: GPT-6 Sol and Luna role upgrades
- Require three distinct Architect designs, one per configured runner, before synthesis; verified Sol high, Astra low, and Fable 5.1 high through a complete design-only dry run.
- Set Arena runners to Astra medium, GPT-6 Sol high, GPT-5.6 Sol high, Opus 5.5 high, and Fable 5.1 high; route both Claude candidates through `claude -p` and require Claude Code 2.1.280+ for Opus.
- Upgrade active Luna roles to GPT-6 Luna at high reasoning: discovery, Swarm, comment audits, and live-verification lanes; align the plan validator and setup template.
- Upgrade active Sol roles to GPT-6 Sol at high reasoning: Arena runners and cross-judge pool, Architect, Interrogate, implementation playbooks, explainers, synthesis, tooling reflection, and Codex-first defaults; keep setup templates aligned.

## 2026-09-17: Design panel models
- Architect now uses Sol high, Astra low, and Fable 5.1 high; Arena honors the design panel and runs its Fable candidate through Claude CLI.

## 2026-09-14: PStack setup reasoning budgets
- Ported upstream PStack `5bf2b1544d`: `setup-pstack` now offers four reasoning budgets, records the choice, and validates each model's supported effort before writing per-role settings.

## 2026-09-13: PStack port bumped to upstream 889ec4b, hardened scripts, six team-kit skills
- Regenerated the port at `cursor/plugins` `889ec4b`; upstream moved bug-fix, perf-issue, and hillclimb to its fast code model, which the port already rendered as `gpt-5.6-sol` at `high`, so only the surrounding prose changed.
- Replaced the poteto-mode scripts with the hardened set from [michael-denyer/pstack-claude](https://github.com/michael-denyer/pstack-claude) (v0.9.29): the PR watcher reads every review-thread page, rejects non-advancing cursors, and checks the head SHA stayed put under one deadline; the orch store serializes mutations and splits into `frontier.ts`, `status.ts`, `types.ts`; `worktree-audit.sh` parses NUL-delimited records and runs on GNU and BSD coreutils; `check-plan.mjs` handles tilde fences and requires a box per task; `bootstrap.ts` refuses node and installs production deps only. Re-applied the two Codex edits (rollout transcripts path, plan markers). 79 tests pass.
- Added `fix-ci`, `fix-merge-conflicts`, `get-pr-comments`, `make-pr-easy-to-review`, `thermo-nuclear-code-quality-review`, and `what-did-i-get-done` from the Cursor team kit, verbatim plus the `_Source:` line and MIT license, the same way `deslop` was added.
- Rewrote `poteto-mode/references/models.md` as the upstream `pstack-models.mdc` rule word for word: one `role: model` line per role with the same labels, `inherit-parent`/`auto` aliases, and `<slug> at <effort>` values that map to a collaboration agent's `model` and `reasoning_effort`. `setup-pstack` is now generated from upstream too, and its step 5 template is that file verbatim.
- Budget routing in `models.md`: Astra stays only on the three decisive single-call roles (judgment and prose, hardest tasks, reflect judgment) plus one interrogate arm and the cross-judge pool; explainers and synthesizers move to Sol high, arena and architect panels run Sol, Terra, and Luna. Per the September usage analysis, effort is not the cost lever, the model's input rate times context is, so the change is which roles touch Astra, not their effort.
- The generator now derives every inline model default from `models.md` by role (single-role defaults, the arena and architect panels, the cross-judge pool, swarm workers, poteto-mode's spawn defaults, and the interrogate reviewer table), so the skills and the file cannot disagree.
- poteto-mode's spawn defaults now name `fork_turns: "none"`: Codex forks the parent's entire context into every collaboration agent unless told otherwise, and the dry run showed a poteto-mode explainer spawned with `fork_turns: "all"`, inheriting a 500K-token parent. Verified on a live `codex exec` run: skills resolve from `~/.codex/skills`, the models file is read at its `${CODEX_HOME}` path, and spawned agents carry the role's model and `reasoning_effort`.
- The generator now mirrors upstream's `disable-model-invocation: true` into `agents/openai.yaml` as `policy.allow_implicit_invocation: false`, which is how Codex keeps a skill out of the implicit skill list while leaving it readable by path (the 2026-09-03 port already did this by hand for 40 skills; `automate-me`, `recall`, `tdd`, `typescript-best-practices`, `unslop`, and `thermo-nuclear-code-quality-review` now match). A `codex exec` dry run confirmed the hidden set is exactly what Codex omits from its skills list, and that the remaining 68 listed skills fit the 2% skills context budget without truncation.
- Added a `Comment Sicko` role to `models.md` on `gpt-5.6-luna` at `high`; `no-comments` names it, so the comment audit no longer inherits the Astra judgment default.

## 2026-09-12: PStack port regenerated from upstream
- Rebuilt every ported PStack skill from upstream `f5bdd68` by minimal substitution (`port-upstream.py` alongside the review report), so each file is upstream word for word except the Codex parts: `/goal` for `/loop`, `update_plan` for the todolist, `$name` invocation, Codex collaboration agents with `model` and `reasoning_effort` in place of `Task` fields, `skill-creator` for `create-skill`, mirror paths under `${CODEX_HOME:-$HOME/.codex}/skills`, and Codex rollouts for transcripts.
- Added a per-role model table at `poteto-mode/references/models.md`, the Codex stand-in for `~/.cursor/rules/pstack-models.mdc`, and pointed every routed skill at it; ported `setup-pstack` around it.
- Added `automate-me`, `recall`, `teach`, `control-cli`, `control-ui`, `principle-attack-the-premise`, and `principle-test-behavior-not-implementation`; dropped the orphaned `how` critic prompts and the Pocock `tdd` references, since `tdd` now follows PStack.
- Replaced the poteto-mode scripts with upstream verbatim plus `bootstrap.ts`, which self-installs dependencies, removing the prebuilt `dist/` bundles; only the transcript path in `worktree-audit.sh` and the markers in `check-plan.mjs` differ.

## 2026-09-11: Reviewed PStack refresh and deslop
- Added the Cursor team kit `deslop` skill for stripping AI code slop from a branch diff, alongside the prose-focused `unslop` and the comment-focused `no-comments`.
- Landed the reviewed upstream text for `architect`, `blast-radius`, `create-verification-skill`, `figure-it-out`, `how`, `interrogate`, `maintain-verification-skill`, `make-bot-ui`, and `no-comments`, keeping the local `$name` invocation form and omitting Cursor-only frontmatter.

## 2026-09-08: PStack upstream refresh and model roles
- Reconciled the Codex PStack port through upstream `23a56e2`: retained the already-ported forge-neutral PR and stack workflows and recorded the Cursor-only metadata and packaging that Codex cannot accept.
- Routed Astra at medium reasoning to orchestration, judgment, synthesis, and primary review; Sol at high reasoning to implementation; Luna at high reasoning to discovery and procedural verification; and Fable 5.1 at max reasoning only to optional independent review. Autoreview now enforces the same review defaults and no longer falls back from Astra to Sol.
- Added PStack's `typescript-best-practices` skill and patterns reference at upstream `23a56e2`, omitting Cursor-only frontmatter, plus a fail-closed Codex adaptation of `make-bot-ui` that requires an existing webhook and server-side secret path when no webhook-routine tool exists.

## 2026-09-06: Astra Reasoning Defaults
- Defaulted routine Astra work in PStack skills and Poteto playbooks to medium reasoning; retained high for reviews and reasoning-heavy tasks, including Autoreview, with fast mode still forbidden.

## 2026-09-04: Autoreview Astra Default
- Changed the autoreview skill and helper default to `gpt-6-astra` at high reasoning, using Sol as the access-only fallback and preserving explicit model selection; skill instructions require standard mode.

## 2026-09-04: PStack Astra Routing
- Made `gpt-6-astra` the PStack default for implementation and synthesis, including Poteto playbooks; retained `gpt-5.6-sol` in mixed-model reviews, Arena candidates, and independent audits. All routes use high reasoning and never fast mode.

## 2026-09-03: Codex Poteto Mode
- Added all 21 PStack principle skills plus a Codex-native `poteto-mode` router with Lauren Tan's playbooks, orchestration ledger, PR watcher, explicit-only invocation, safe Codex write boundaries, matching verification surfaces, and role-based high-reasoning model routing with no fast mode.
- Added `~/.agents/skills` as a mirror destination only; `scripts/sync-skills` rejects a symlinked root before normal or dry-run work can touch its backing tree and tracks links it creates or retargets so deleted local skills do not return through another mirror.

## 2026-09-02: Codex PStack Skills
- Added a Codex-native port of PStack's `how` workflow for codebase explanations and architecture critique, with Luna explorers, Sol explainers and critics, high reasoning, and no fast mode.
- Added Codex-native ports of PStack's `why` and `technical-writing` workflows, preserving the upstream text outside Codex routing, tool, concurrency, and model adaptations; `why` uses Luna investigators and a Sol synthesizer at high reasoning with no fast mode.
- Restored `create-verification-skill` to PStack's upstream wording, changing only Codex skill paths, invocation syntax, metadata, and authorization boundaries.
- Restored `maintain-verification-skill` to PStack's upstream wording, changing only Codex skill paths, invocation syntax, source-reader concurrency and model settings, metadata, and authorization boundaries.
- Added Codex-native ports of PStack's `swarm`, `arena`, `interrogate`, `reflect`, `figure-it-out`, `show-me-your-work`, `no-comments`, and `bro` skills, preserving upstream wording outside Codex plans, collaboration agents, transcript paths, invocation syntax, permissions, and role-based high-reasoning model routing with no fast mode.

## 2026-08-26 — Codex Verification and Eval Skills
- Added a Codex-native port of PStack's `create-verification-skill`: repo interview, native `.agents/skills/verify-<app>` generation with a protected-directory fallback through `skills/` plus `AGENTS.md` routing, real user-path proof, feature-map examples, safe process ownership and cleanup, authorization boundaries, MIT attribution, UI metadata, validation, and shared skill discovery.
- Added the companion `maintain-verification-skill`: complete source and live feature coverage, drift and regression triage, safe doctor and cleanup invariants, optional authorized source-reader delegation, and no automatic branch, commit, push, or PR.
- Added `eval-skill`: blinded skill-versus-baseline trials in sanitized isolated projects, held-back observable rubrics, model-balanced pairs, one shared blind judge, transcript evidence when available, artifact-first grading, and explicit promote, reject, or inconclusive outcomes.

## 2026-08-19 — Recent Skill Refresh
- Replaced the retired `to-issues` route with `to-tickets`, refreshed the Matt Pocock TDD/setup/ticket bundle from current upstream, upgraded Peekaboo CLI and guidance to v4, and updated browser automation for cmux-first routing plus fail-closed Chrome extension relay use.

## 2026-08-19 — Diagnosis, Design, and Writing Skills
- Added Matt Pocock's `diagnosing-bugs` workflow plus minimally adapted Codex-native copies of PStack's `architect` and `blast-radius`, and an unchanged PStack `unslop` workflow, with upstream attribution, MIT notices, UI metadata, validation, and local skill-mirror discovery.

## 2026-08-12 — Agent Performance Audit
- Added a reusable personal skill and deterministic CLI for repository-scoped Codex-history audits with separate Claude activity coverage, injected-prompt exclusion, correction and shell-tool-output denominators, cumulative-delta per-turn token accounting, baseline comparisons, redacted causal notes, privacy validation, and self-contained local HTML reports.

## 2026-08-12 — External-State Recovery Boundary
- Added a global recovery rule plus PatchProof, 1Password, and maintainer-loop guidance: terminate only verified task-owned processes, preserve diagnostics, never mutate another application's caches/databases/configuration/credential state without exact approval, and stop after documented task-local recovery fails.

## 2026-08-12 — Maintainer Loop Structured Monitoring
- Replaced repeated worker transcript polling with batched cursor-based waits, a compact current-state ledger, explicit 5/15/30/60-minute backoff, targeted raw-history recovery, and counters for verifying heartbeat and automation overhead reductions.

## 2026-07-22 — Autoreview From Canonical Source
- Replaced the vendored `autoreview` skill with the canonical `openclaw/agent-skills` copy at `c4ab5e7` (helper 2,485 -> 12,001 lines), including its scripts, test suite, fixtures, and the skill-level `AGENTS.md` sync rule.
- Gains TruffleHog secret scanning over the reviewed diff, a Scope Governor that classifies findings as in-scope blocker / follow-up / stop-and-escalate, oversized-bundle handling, release-branch rules, and Codex `gpt-5.6-sol` with an access-only fallback to `gpt-5.6-terra`.
- Engines that cannot be fully isolated (`droid`, `copilot`, `opencode`, `cursor`) are now refused rather than run; `--preset` is gone, so the AGENTS rule for API work uses `--engine claude --model claude-opus-4-8`.
- TruffleHog is a hard requirement: autoreview exits early when it is not on PATH.

## 2026-07-22 — Validator UTF-8 Fix
- `scripts/validate-skills` reads `SKILL.md` as UTF-8 instead of inheriting the process locale, so validation and the pre-commit hook stop failing with `invalid byte sequence in US-ASCII` in shells without `LANG` set.

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
