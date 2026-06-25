---
name: bram-maintainer-loop
description: "Orchestrate Bram repo maintenance loops across flagged repositories: triage queues, delegate workers, monitor, prepare decision-ready PRs, and gate with TDD/tests/autoreview."
---

# Bram Maintainer Loop

Coordinate repository work through completion. This is a control-plane skill: inspect, delegate, monitor, ask decisions, and report. Put substantial repository investigation, implementation, review, live proof, landing, and release execution in repository worker threads.

This skill is adapted from upstream `maintainer-orchestrator`. Keep the proven loop mechanics; Bram-specific differences are scope, secrets, release authority, and use of `tdd`, `to-prd`, and `to-issues`.

## Repository Scope

- Default scope is the current GitHub repository when the request starts inside a repo.
- Broad scope is the flagged repo list at `~/Projects/agent-scripts/config/bram-loop-repos.txt`.
- During worktree tests, an explicit config path supplied by Bram may stand in for the canonical flagged repo list.
- Initial flagged repos: `gohealthcli`, `gobankcli`, `goggquote`.
- Resolve flagged repo names under `~/Projects/<repo>` first; missing Bram repos may be cloned from `https://github.com/BramVR/<repo>.git` only when the user asks to work on them.
- After resolving a local repo, derive the canonical GitHub `owner/name` from its `origin` remote. Local folder/config casing may differ from GitHub repo casing, for example `gobankcli` -> `BramVR/goBankCli`.
- Exclude archived repositories from routine discovery, queue scans, dependency audits, monitoring, release gating, and reporting. Re-enter only when Bram explicitly names the repository.
- When Bram says a repository is retired, archived, or must not be mentioned again, record it as suppressed. Make an archive mutation only when explicitly requested, then keep it silent even when permissions prevent the remote archive.
- Hermes is optional proof/infra scope only. Use `hermes-win` when the task needs Windows/Home Assistant/remote-host proof; do not treat Hermes as a default queue.
- Keep a current repository ledger so completed lanes are replaced by real queue, CI, dependency, or documentation work.

## Operating Model

1. Use `github-project-triage` to map each repository's open issues, open PRs, CI, latest release, package metadata, docs/changelog state, and local dirty state.
2. Classify every queue item:
   - `Autonomous`: clear fit, reproducible, bounded implementation, and usable verification path.
   - `Needs Bram`: product choice, security/privacy decision, unavailable credential/access, unavailable live proof, or destructive/irreversible choice.
   - `Ignored by Bram`: an explicitly named item Bram says must not affect current work or release gating.
3. When delegation is explicitly authorized, this root loop session delegates repository triage/backstop lanes to Codex threads. Workers use `github-project-triage` as both the queue mapper and the issue/PR workhorse; do not create a separate workhorse skill. Whenever assigning or materially changing work, rename the worker thread to `<Project>: <short current task>`. For a newly selected GitHub issue, always create a fresh dedicated issue worker thread; reuse a worker only for the exact same issue already in progress. Create worker threads with `gpt-5.5` and `high` reasoning unless Bram explicitly overrides for that lane.
4. Keep this coordinator thread lightweight. Do not perform extensive repository work here. Delegate it to a repository thread, then monitor by reading current state.
5. On continuous orchestration or e2e loops, create or update a Codex heartbeat automation for this coordinator when the platform automation tool is available. The heartbeat is the wakeup clock; the prompt cadence is only the in-turn behavior. Monitor workers without Bram nudges; do not stop merely because workers or CI are still active.
6. Continue until each autonomous item is merged with proof when merge permission is granted, each decision item is prepared to the last authorized boundary, an empty effective queue has either an explicitly authorized gated release completed or a documented no-release/needs-authorization reason, or an otherwise idle repository has current dependencies/docs.

Do not treat ordinary draft, stale, difficult, or platform-specific items as ignored. Only an explicit Bram instruction can create an ignored-item exception. Keep ignored items open and visible; do not close, edit, or merge them unless separately requested.

## Flagged Repo List

Read `~/Projects/agent-scripts/config/bram-loop-repos.txt` for broad loops. One repo slug per line. Blank lines and `#` comments are ignored.

Recommended initial loop:

```text
gohealthcli
gobankcli
goggquote
```

When Bram asks to add or remove loop repos, edit that config and keep the change terse.

## Control-Plane Ownership

- Only this root loop session may create, reuse, fork, assign, rename, archive, or steer worker threads.
- New GitHub issue implementation work gets a fresh dedicated worker thread, even when the repository already has an idle or completed worker. Reuse only the worker already assigned to that exact issue.
- Repository workers perform only their assigned repository work and report results to this loop. They must not create subworkers, delegate work, or manage other chats.
- Put the no-subdelegation rule in every worker prompt.
- Do not delegate portfolio triage, thread creation, or worker management to another worker.
- Legacy nested coordinators: stop further delegation immediately, preserve unique context while their existing workers finish, then retire them after reading current state.

## Decision-Ready Queue Rule

Do not ask Bram to decide from an unprepared issue or rough contributor branch.

- Existing PR: inspect, reproduce, rewrite/fix as needed, add tests/docs/changelog, run live proof, pass the Review Gate below on the final candidate, push the final candidate, and get required CI green. When merge is authorized and all gates pass, merge it; otherwise ask only when the PR is mergeable or the remaining blocker cannot be solved autonomously.
- Issue without PR: investigate root cause and product constraints, use `tdd` for implementation when code behavior changes, implement the best bounded candidate on a branch, create a PR with a closing keyword for the assigned issue when correct, and drive it to the same mergeable proof state. When merge is authorized and all gates pass, merge it.
- Vague feature/product idea: use `to-prd` or `to-issues` before implementation when the request is too broad for one autonomous slice.
- Product decision: choose a reversible default when technically safe and expose the decision clearly in the PR. Prepare alternatives in the PR description when useful.
- Access or live-proof blocker: finish code, tests, docs, required review, and CI first. Ask only for the exact remaining credential, account action, hardware interaction, waiver, or land/delete decision.
- Rejection candidate: produce concrete research and proof. When a code candidate would clarify the tradeoff, prepare the PR anyway; otherwise update the issue with the evidence needed for a Bram close/keep decision.

The normal Bram interaction should be one of: delete/close a prepared PR, provide one exact access step, grant one explicit waiver, choose between clearly documented alternatives, or land the prepared PR only when merge permission is absent or blocked by protection.

When Bram asks to manually test a PR, treat that as an explicit stop-before-merge boundary. Prepare a non-draft PR with gates, live proof, confidentiality pass, and exact manual test commands, then stop without merging until Bram gives new merge authority.

## Review Gate

Run one basic review per stable candidate. Do not run a full pre-PR review and then repeat the same review before merge when the reviewed commit is still the merge candidate.

- `Basic`: every candidate, including docs, metadata, formatting, and test-only changes. Run relevant tests/checks, then default `autoreview` until no accepted/actionable findings remain.
- `Extra`: auth, secrets, privacy, external integrations, public artifact/log/screenshot/model-bearing changes, broad refactor, contributor PR rewrite, release candidate, breaking dependency, unclear behavior, or anything that failed basic review for non-trivial reasons. Add `autoreview --preset claude-opus` until clean when the extra risk justifies it or Bram asks for it. If Claude Opus is unavailable, report that the extra review is unavailable instead of treating it as routine failure.

Before merge, refresh the PR diff, CI, review state, and mergeability. Re-run the Review Gate only when candidate code, generated artifacts, public proof, or risk level changed after the last clean review. PR body edits, CI reruns, rebases with no effective diff change, or test/proof output updates do not require another review.

## Owner Decision Briefs

Never ask for `land/delete`, approval, access, waiver, or a product choice with only a URL or status label.

Immediately before asking, refresh the item and worker state. Do not repeat a question Bram already answered, and do not present an item as decision-ready when it has become conflicted, stale, red, or otherwise moved behind an autonomous repair gate.

Every decision request must include:

- full canonical clickable URL and title when the item exists on GitHub;
- plain-language explanation of what changes and who benefits;
- why the decision is needed now;
- completed proof: reproduction, live test, tests, Review Gate result, CI, and mergeability as applicable;
- material tradeoffs, residual risks, scope concerns, or missing evidence;
- the loop's recommendation and concise rationale;
- the exact choices available and what each choice does.

When several decisions are grouped, give each item its own brief. Keep the recommendation opinionated; do not offload technical analysis to Bram. If autonomous work remains, do that work first and report the item as active rather than asking for a premature decision.

## Monitoring Protocol

Assume another person or agent may have steered every worker since the last poll.

Heartbeat wakeup:

- At loop start, use the Codex app automation tool to create or update one heartbeat automation attached to this coordinator thread.
- Default schedule: every 5 minutes.
- Heartbeat task: refresh coordinator, worker, PR, and CI state; continue the loop; send worker messages only for the intervention cases below; close out only at a blocker, permission boundary, no safe work remains, or stable decision-ready state for work that cannot be merged under current permissions. Do not stop at a green mergeable loop PR when merge permission is granted.
- Prefer updating an existing matching maintainer-loop heartbeat over creating duplicates.
- If the automation tool is unavailable, say so in the first status and continue with in-turn timed polling.

Default cadence:

- newly created worker or active TDD/review/PR setup: poll every 60-120 seconds;
- queued/pending worktree setup: poll every 30-60 seconds until the worker exists or a concrete setup blocker appears;
- CI watch after PR creation: poll every 60-180 seconds until green, red, or cancelled;
- long-running but healthy worker: poll every 5 minutes after at least two coherent progress checks;
- after any worker becomes idle/completed: refresh its final answer, PR/CI state, and the repository queue before reporting.

The coordinator owns this cadence. Do not wait for Bram to type "check", "status", or "done?" before the next poll. Do not send a final answer while any delegated worker, required CI, or authorized repair loop is still active unless a precise blocker or permission boundary has been reached.

Before sending any worker message:

1. Read the worker's latest current state, including newest user/delegation messages and active turn.
2. Treat the newest thread-local instruction as authoritative over older orchestration plans.
3. Determine whether the worker is actively progressing, blocked, completed, or idle.
4. Send nothing when an active worker has a coherent plan and is making progress.

Intervene only when evidence shows one of:

- the worker explicitly requests coordination or reports a blocker;
- Bram reports live/manual behavior that contradicts the worker's scripted proof, such as stuck UI, wrong output, missing action, or proof that does not show the real surface;
- the worker has completed or run out of autonomous work and needs a next queue item;
- repeated failures show no progress and a concrete correction is available;
- wrong repository/item, unauthorized mutation, destructive action, security risk, release-gate violation, or direct conflict with Bram's latest instruction;
- implementation has grossly diverged from the accepted task, not merely chosen a different reasonable design.

Do not restate the task, add speculative requirements, or raise the proof bar mid-flight. Apply the live-proof gate from initial delegation; never downgrade missing live proof to a release-only blocker. Prefer one concise question over prescriptive steering when current intent is ambiguous.

When Bram materially changes behavior, scope, wording, or proof expectations mid-flight, update the GitHub issue/PR or worker prompt so the latest source of truth is durable. Do not leave future workers to infer the correction from chat history.

Never interrupt, archive, rename, duplicate, or replace a worker without first reading its current state. For a suspected duplicate, read both threads; if either has unique progress, edits, or an active turn, leave it alone and ask Bram before changing thread state.

## Thread Naming

- Rename a worker whenever giving it a new task or materially changing its assignment.
- Format every worker title as `<Project>: <short current task>`.
- Read the latest state and newest thread-local instructions before renaming.
- Keep the title specific to current work; replace stale original-task titles.
- Polling alone does not justify a rename.

## Persistent Log

- This root loop owns one markdown ledger under `~/.codex/state/bram-maintainer-loop/`; workers do not edit it.
- Use one file per loop, not one global append-only file. Name it `YYYY-MM-DD-<short-loop-slug>.md`, for example `2026-06-14-gobankcli-site.md`.
- At loop start, create or announce the ledger path. If continuing an existing loop, reuse that loop's ledger rather than starting a new file.
- Append dated, high-level entries for meaningful actions and decisions: policy/skill changes, worker creation or reassignment, queue decisions, lands, closes, releases, and exact blockers.
- Include full canonical issue/PR URLs when relevant.
- Never record secrets or routine polling.
- Skip log writes when Bram explicitly requests read-only, no-edits, or dry-run behavior; report that the log append was intentionally skipped.

## Idle Thread Closeout

An idle or completed repository thread must not remain a polling-only lane. After reading its latest state, inspect that repository's current queue, CI, latest release, package metadata, docs/changelog state, and flagged repo priority. Then do exactly one:

1. Assign the next autonomous PR to the same repository thread, or assign the next autonomous issue to a fresh issue-specific worker thread.
2. Prepare each remaining non-autonomous item to the decision-ready boundary, then ask Bram a concise concrete question.
3. When the effective issue and PR queues are empty, execute the authorized patch or minor release after all release gates pass.
4. If no queue, CI, or authorized release work remains, treat dependency freshness as the next candidate backstop. When implementation is authorized, or when delegation is separately authorized, audit and update dependencies to compatible current stable releases unless Bram authorizes breaking-major upgrades. Delegate this as normal repository work: inspect upstream changes and package health, honor repository-specific stabilization policies, avoid prerelease-only upgrades unless already adopted, preserve the repository's package manager, add compatibility fixes/tests when needed, run exact built/live proof, pass the Review Gate, pass the Public Artifact Confidentiality Gate, and required CI, then prepare or land the update within granted permissions. Without implementation/delegation authorization, report dependency freshness as the next candidate work and stop.

Do not keep completed threads merely to satisfy a lane count. A monitored repository should have active autonomous work, a pending Bram question, an active release, or a documented no-release/needs-authorization reason.

Dependency freshness is a backstop, not higher priority than real queue, CI, or release work.

Architecture review is a backstop and recommendation lane, not an automatic worker step. When repeated workers report hard-to-test modules, shallow modules, unclear seams, or cross-cutting refactor pressure, report `improve-codebase-architecture` as `Ready next` for Bram to invoke separately. Do not run it inside the loop unless Bram explicitly asks for an architecture pass.

## Authorization

Treat triage, monitoring, implementation, public mutation, and release as separate permissions.

Starting a continuous maintainer loop or e2e loop authorizes creating or updating the coordinator heartbeat automation unless Bram says read-only, dry-run, no-edits, no-automation, or similar. The heartbeat must only monitor and continue this loop; it does not authorize extra repository mutations beyond the loop's granted permissions.

When Bram explicitly asks this loop to handle a specific issue or PR in a Bram-owned repository, and does not say read-only, dry-run, no-edits, plan-only, audit-only, or similar, that request authorizes: resolving or cloning that repo if missing, creating or checking out a focused branch in the repo checkout when clean enough to do so, implementing the bounded candidate, committing, pushing the branch, creating or updating the PR, rerunning/watching required CI, and making repair commits until CI is green. It does not authorize merge, close, release, destructive local cleanup, unrelated workflow/secret changes, or broad work outside the named item.

Read-only, no-edits, dry-run, plan-only, or audit-only overrides all mutation permission: no local edits, branch checkout, commits, pushes, PR/issue comments or creation, CI reruns, worker thread creation/renames, or loop log writes. Report findings, proposed branch/PR plan, and the exact next permission needed.

If the target checkout is dirty, on an unexpected user branch, or otherwise cannot safely switch/create the issue branch, stop and ask Bram for the exact checkout action. A clean Codex-managed worktree with detached `HEAD` is acceptable when `origin/main` resolves; create the focused issue branch from current `origin/main`. Do not create a new worktree to bypass a blocker unless Bram asks.

- Queue analysis or monitoring does not authorize edits.
- Delegation or parallel-worker creation requires explicit Bram authorization.
- Implementation permission authorizes local changes and verification only unless Bram also authorizes push/PR updates or gives the specific issue/PR handle grant above.
- Push permission does not imply merge or close permission.
- CI rerun and CI-fix permission must be explicit unless Bram gives the specific issue/PR handle grant above; a push alone does not authorize workflow mutations.
- Merge/close permission must be explicit for the affected work. When merge is granted for a maintainer loop, merge only loop-prepared or loop-repaired PRs after all required proof is complete: focused tests, full gate, live proof or explicit waiver, Review Gate pass for the current candidate, Public Artifact Confidentiality Gate, non-draft PR, required CI green, no unresolved requested-changes review, and no fresh Bram instruction blocking the change. If branch protection, stale base, conflicts, red checks, or review requirements block merge, repair autonomously when authorized; otherwise ask with the exact blocker.
- Merge permission does not imply manual issue close, release, destructive cleanup, or unrelated PR merges. Prefer PR closing keywords for assigned issues; do not manually close issues unless close permission is also granted.
- Release, version bump, tag, registry publish, and GitHub Release require a current explicit release request.
- Release permission must explicitly include required branch/tag pushes or be paired with push permission.
- `ship` uses repo `AGENTS.MD` meaning: changelog, commit in groups, push, pull.
- `fix ci` authorizes pull, commit, push, rerun/watch until green for that CI task.

Record the granted permissions in each worker prompt. Without the required permission, stop at the last authorized boundary and report the exact next action.

## Credential Access

Do not make the loop depend on secrets. Most queue triage, issue slicing, tests, and static review should run without credentials.

When a task requires credentials:

1. Check only the exact expected environment variable; prefer `~/.profile` for known env names.
2. Read the service-specific auth skill if one exists.
3. Use `$one-password` only for exact known item/field access, tmux-only, following repo `AGENTS.MD`.
4. Never broadly enumerate secrets or print values.
5. Ask Bram only after the targeted environment/1Password path is absent, inaccessible, or requires interactive unlock/approval.

Keep credential discovery and use inside the worker that needs the secret. Report only presence, access path, and the exact missing approval or item; never send credentials between threads.

## Worker Contract

Every delegated implementation thread, within its explicit authorization, must:

- use `github-project-triage` Autonomous Work Mode for the assigned item;
- read the full issue/PR discussion, repo instructions, docs, and relevant code;
- when an issue has no PR, create one after implementing the best bounded candidate;
- when work is broad or vague, use `to-prd` or `to-issues` before implementation;
- when Bram names a comparable repo or implementation pattern, inspect that source before designing; copy the proven pattern where it fits, and invent only after explaining why reuse is blocked or wrong;
- when changing code behavior, use `tdd` unless the change is too trivial or docs-only;
- reproduce or establish root cause before accepting an existing patch;
- rewrite when a cleaner bounded design is available;
- add regression coverage when appropriate;
- run focused and full tests, then live/end-to-end proof against the real affected boundary before landing;
- pass the Review Gate for the final candidate; do not repeat the same review before merge unless the candidate or risk changed;
- when push is authorized, push the authorized changes;
- when CI rerun/fix is authorized, rerun required checks and repair failures until green;
- when CI rerun/fix is not authorized and checks fail, stop with the exact failure and requested permission;
- when merge is authorized, merge the prepared PR only after all merge gates pass, then fetch/pull `main --ff-only`, verify clean status, refresh the queue, and continue to the next autonomous item;
- when close is authorized, close the queue item with exact proof;
- after authorized landing, return to updated, clean `main`.

Prefer repairing the contributor PR. Preserve contributor credit and follow workspace PR rules.
When landing is not yet authorized, stop only after the branch is pushed, the PR is mergeable, required CI is green, live proof is recorded, and the exact Bram decision is stated.

## Live Proof Gate

Live proof is a pre-land requirement for runtime behavior, not optional polish.

- Test the exact final candidate commit through the changed user path using the real built/installed artifact and real service, account, device, OS, or external provider as applicable.
- For external integrations, authenticated live calls are required when credentials are available. Docs, mocks, fixtures, protocol captures, route-existence checks, and CI supplement live proof; they do not replace it.
- Redact secrets and private user data while retaining concrete evidence such as command, behavior, response class, artifact hash, or observed state transition.
- If credentials, account state, hardware, platform access, or a safe live target are unavailable, finish all autonomous code, tests, required review, and CI work, then stop before merge/close. Ask for the exact access, an explicit item-specific waiver, or a reject/close decision.
- Never infer a live-proof waiver from merge permission, release permission, prior contributor evidence, or confidence in mocks.
- Re-run live proof after any fix that changes the relevant runtime path.
- Pure docs, metadata, CI, or test-only changes with no runtime boundary may use the closest built-artifact or workflow proof; state why no external live boundary applies.
- When UI screenshot proof is requested, capture the actual running UI surface being changed (app window, native menu, status item, browser viewport, etc.). Do not substitute generated artifacts, SVG renders, diagrams, fixture cards, or model-only proof unless Bram explicitly accepts that waiver.
- Public UI proof must render where reviewers will read it. Prefer GitHub `user-attachments`/`gh image` or another verified inline-rendering path; do not call raw branch links, local paths, private raw URLs, or unrendered generated files sufficient proof.

Record live evidence or Bram's explicit waiver in the landing proof comment.

## Public Artifact Confidentiality Gate

Before any push, public PR update, merge, or release involving secrets, model identifiers, private endpoints, personal data, generated logs, screenshots, or public artifacts:

- Audit the exact candidate diff, tests, fixtures, snapshots, generated metadata, workflows, CI/test logs, packaged artifacts, and public PR/issue proof.
- Do not expose non-public organizational information, credentials, URLs, datasets, personnel details, internal model names, or proprietary context.
- For model-bearing code or artifacts, audit specifically for model identifiers.
- Public model identifiers may remain only when they are currently documented or offered in an official public provider source. Record the source URL in the worker's audit report.
- Never expose internal, employee-only, preview-only, alias-only, inferred, synthetic provider-shaped, or otherwise undisclosed identifiers. Genericize questionable test and fixture values because assertion failures can print them in CI logs.
- Do not repeat questionable secret-like, internal, or unverified model identifier strings in worker messages, audit reports, public comments, or the loop log. Describe them generically.
- Binary/archive scans must classify candidate strings as verified public identifiers, unrelated false positives, or blocking unknowns without echoing blocking unknowns.
- Return an explicit `PASS` or `BLOCKED` report covering every audited surface. Any new candidate diff, generated artifact, log/proof text, or model-bearing change invalidates the pass and requires re-audit.

No push, public mutation, merge, or release may proceed while this gate is blocked.

## Release Gate

Compute the effective queue immediately before release:

```text
effective issues = open issues - explicitly ignored issues
effective PRs    = open PRs - explicitly ignored PRs
```

Release only when all are true:

- Bram explicitly requested this release or authorized release execution for the repository;
- effective issue count is zero;
- effective PR count is zero;
- every ignored item is explicitly named in current Bram instructions;
- required CI is green for the exact commit and branch/tag candidate;
- user-facing runtime changes have required live proof unless Bram explicitly waives proof for the release;
- release checkout is clean, on the expected branch, and fast-forward current;
- unreleased changes justify a release and the target version follows project convention.

Recheck GitHub queue and CI immediately before tagging or publishing. Abort if either gate changes.

Never silently exclude an item. In release reporting, list ignored items and the Bram instruction that exempted them.

## Release Execution

Use the repository's release docs and matching skill:

- npm packages: use `npm`;
- macOS apps: use repo release docs and any matching release skill;
- other projects: use established repo scripts/workflows.

If release docs, changelog, tags, or CI/release workflows are missing, do not infer a release path. Report the missing release lane and prepare docs/workflow improvements only when authorized.

Before release:

- reconcile changelog history with existing tags/releases;
- default to patch for compatible fixes, maintenance, refactors, docs, CI, and small behavior improvements;
- select minor only for substantial additive functionality, a meaningful new feature set, or a new backward-compatible public API;
- never use minor merely because several fixes accumulated; major requires explicit approval;
- run full release checks, pass the basic Review Gate on release-only edits, and add Claude Opus extra review when release risk justifies it or Bram asks for it.

After publishing, verify the actual release:

- Git tag and GitHub Release exist;
- release notes contain the complete changelog section;
- expected artifacts/install path work;
- npm packages show version, dist-tag, tarball, integrity, and publish time;
- release body links registry/artifact/integrity and CI proof when applicable.

Then open the next patch `Unreleased` section. Commit and push closeout only when those mutations are authorized; otherwise leave the verified local closeout ready and report the exact permission needed. After an authorized push, pull `--ff-only` and finish on clean `main`.

## Reporting

Keep one compact cross-repo ledger:

- `Active`: repo, item URL, worker, current phase.
- `Intervened`: exact risk and instruction sent.
- `Needs Bram`: exact decision/access required; no vague "needs review".
- `Ignored`: exact item and Bram-granted exception.
- `Released`: version, tag/registry verification, closeout commit.
- `Ready next`: effective queue empty; if release lane/proof are known and CI is green, recommend patch/minor version and rationale; otherwise report exact missing release gate or permission.

Omit archived and Bram-suppressed repositories entirely. Do not list them as ignored, blocked, stale, or available work.

Whenever mentioning an issue or PR in any report, decision question, worker message, or status update, print its full canonical clickable URL. Never use only a repository-local number such as `#123`; include `https://github.com/OWNER/REPO/issues/123` or `https://github.com/OWNER/REPO/pull/123`.

Report meaningful changes, not routine polling. Maintain a heartbeat automation when Bram asks to keep monitoring.
