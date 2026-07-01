---
name: bram-maintainer-loop
description: "Current-repo maintainer loop: issue workers, TDD, autoreview, CI, proof, releases."
---

# Bram Maintainer Loop

Coordinate repository work through completion. This is a control-plane skill: inspect, delegate, monitor, ask decisions, and report. Put substantial repository investigation, implementation, review, live proof, landing, and release execution in issue or PR worker threads.

This skill is adapted from upstream `maintainer-orchestrator`. Keep the proven loop mechanics; Bram-specific differences are current-repository scope, issue-worker isolation, development workflow, review gates, artifact confidentiality, secrets, and local checkout safety.

## Activation Watch

- Each repository gets its own independent root loop thread. Do not coordinate multiple repositories from one loop unless Bram explicitly asks for a cross-repo loop.
- On every continuous loop activation with automation allowed, immediately create or update one active five-minute heartbeat automation for the current canonical GitHub `owner/name`. Name it `Bram Maintainer Loop Watch: OWNER/REPO`; never create more than one active heartbeat for the same repository.
- If an active heartbeat already exists for the same canonical repository, update that automation instead of creating a duplicate. Treat the heartbeat's attached thread as the repository's root loop unless Bram explicitly moves ownership to the current thread; when ownership moves, retarget the existing heartbeat rather than creating a second one.
- The heartbeat prompt must include the canonical repository, re-enter this skill, read the latest state and newest instructions in every owned worker, apply the Monitoring Protocol, coordinate serialized landing/release gates, triage and refill qualified execution work in that repository, check CI, maintain the persistent log, and surface only prepared Bram decisions.
- Keep the repository heartbeat active while any worker, Bram decision, release, CI wait, or qualified refill work remains. Disable it only when Bram explicitly stops that repository loop or the monitored repository is genuinely complete.
- A heartbeat wake is a continuation of that repository's root loop session, not a discovery worker. Keep repository triage and Bram questions in the repo root loop; create worker threads only for concrete execution.

## Repository Scope

- Scope is the current Git repository.
- Derive canonical GitHub `owner/name` from the repository's `origin` remote.
- If the current directory is not inside a Git repository, stop and ask Bram for the target repo path.
- Do not scan sibling repositories, broad repo lists, or default project inventories unless Bram explicitly asks for a cross-repo loop.
- Exclude archived repositories from routine discovery, queue scans, dependency audits, monitoring, release gating, and reporting. Re-enter only when Bram explicitly names the repository.
- When Bram says a repository is retired, archived, or must not be mentioned again, record it as suppressed. Make an archive mutation only when requested, then keep it silent even when permissions prevent the remote archive.
- Hermes is optional proof/infra scope only. Use `hermes-win` when the task needs Windows/Home Assistant/remote-host proof; do not treat Hermes as a default queue.
- Keep a current repository ledger so completed lanes are replaced by real queue, CI, dependency, documentation, or release work.

## Session Startup

1. Create or update the required repo-scoped `Bram Maintainer Loop Watch: OWNER/REPO` heartbeat before queue work, unless Bram requested read-only, dry-run, no-edits, no-automation, plan-only, or audit-only.
2. Record repository state: `git status -sb`, current branch, upstream, HEAD, staged/unstaged/untracked state, and ahead/behind counts.
3. When mutation is allowed, fetch current remote refs. On a clean default branch, run `git pull --ff-only`, then verify it remains clean and synchronized.
4. Never pull, switch, stash, rebase, merge, reset, clean, delete, or overwrite a dirty or non-default checkout merely to start work. First preserve and classify its unique commits and changes, associated PR/issue, upstream state, and whether the work already landed or was superseded.
5. If local default branch is ahead, diverged, lacks an upstream; fast-forward pull fails; a task branch conflicts with current default; or fetched remote state contradicts the assignment, stop mutation and present Bram with exact commits, files, URLs, conflict, risk, and safe choices.
6. Resume ordinary work only after the checkout is current or Bram chooses how to preserve/reconcile it. Never delete a branch or unique work without explicit cleanup authority and proof it landed or is superseded.

Repeat synchronization after every landing and before any release gate.

## Operating Model

1. Use `github-project-triage` to map the repository's open issues, open PRs, CI, latest release, package metadata, docs/changelog state, and local dirty state. Use it as both the queue mapper and assigned issue/PR workhorse; do not invent a separate workhorse workflow.
2. Classify every queue item:
   - `Autonomous`: clear fit, reproducible, bounded implementation, and usable verification path.
   - `Needs Bram`: product choice, security/privacy decision, unavailable credential/access, unavailable live proof, or destructive/irreversible choice.
   - `Ignored by Bram`: an explicitly named item Bram says must not affect current work.
3. For newly selected GitHub issue implementation work, create a fresh dedicated issue worker thread. Reuse a worker only for the exact same issue or PR already in progress.
4. Do not create discovery, queue-scan, permission-check, candidate-review, ranking, or general triage workers. Use worker threads only for concrete execution after root triage has selected an issue or PR and defined the actual fix, review-and-land, live-proof, CI-repair, or close-with-proof objective.
5. Keep this coordinator thread lightweight. Do not perform extensive repository work here. Delegate it to an issue/PR worker thread, then monitor by reading current state.
6. Continue until each autonomous item is merged/closed with proof, each true decision item has every safe reversible step complete and one exact Bram choice remaining, an authorized release clears its release-specific blockers, or the repository has current dependencies/docs.

Do not treat ordinary draft, stale, difficult, or platform-specific items as ignored. Only an explicit Bram instruction can create an ignored-item exception. Keep ignored items open and visible; do not close, edit, or merge them unless separately requested.

## Immediate Noise Closeout

- Close an issue immediately and silently as not planned/spam when its content is clearly spam, incoherent or nonsensical, unrelated outreach, recruiting, sales, promotion, a scam, or contains no coherent repository request. Do not escalate it to Bram, comment, ask the reporter for repair, or queue implementation.
- Language alone is never a spam signal. Translate and understand foreign-language reports before classifying their content.
- Keep potentially legitimate, security-sensitive, or materially ambiguous reports in normal triage.
- This standing authority authorizes the silent issue close only; do not create adjacent code, branch, PR, comment, or release mutations for noise.

## Control-Plane Ownership

- Only this root loop may create, reuse, archive, or steer worker threads. Root sets the initial `<Project>: <current status>` title. Each worker self-renames after creation so the title follows freshest issue/PR state.
- New GitHub issue implementation work gets a fresh dedicated worker thread, even when the repository already has an idle or completed worker. Reuse only the worker already assigned to that exact issue or PR.
- When creating a Codex worktree worker for a new branch, start the worktree from an existing ref such as `main` or `origin/main`. Put the desired new branch name in the worker prompt and have the worker create/switch it after startup. Do not pass a non-existent new branch as the worktree starting ref; it fails with `invalid reference`.
- Workers perform only their assigned issue/PR work and report results to this loop. They must not create subworkers, delegate work, or manage other chats.
- Put the no-subdelegation rule in every worker prompt.
- Do not delegate repository triage, thread creation, or cross-worker management to another worker.
- Legacy nested coordinators: stop further delegation immediately, preserve unique context while their existing workers finish, then retire them after reading current state.

## Decision-Ready Queue Rule

Do not ask Bram to decide from an unprepared issue or rough contributor branch.

- Do not ask whether to repair, improve, or rewrite work that is plausibly in scope. Make the technical judgment and do the work. Escalate only after every safe autonomous step is complete.
- Treat every incoming PR as a recommendation, not an accepted design. Reproduce the need, then repair, improve, or rewrite it when a cleaner bounded solution exists. Do not ask contributors to perform repair work.
- Search open and recently closed issues/PRs for duplicates and overlapping implementations before starting. Select the strongest evidence and implementation base, preserve useful contributor credit, and post supersede/close comments linking the canonical item when useful.
- Existing PR: inspect, reproduce, rewrite/fix as needed, add tests/docs/changelog, run live proof, pass the Review Gate below on the final candidate, push the final candidate, get required CI green, and land it when evidence supports the change.
- Issue without PR: investigate root cause and product constraints, use `tdd` for implementation when code behavior changes, implement the best bounded candidate on a branch, create a PR with a closing keyword for the assigned issue when correct, drive it through proof/review/CI, and land it when supported.
- Vague feature/product idea: use `to-prd` or `to-issues` before implementation when the request is too broad for one autonomous slice.
- Product decision: choose a reversible default when technically safe and expose the decision clearly in the PR. Prepare alternatives in the PR description when useful.
- Access or live-proof blocker: finish code, tests, docs, review, and CI first. Ask only for the exact remaining credential, account action, hardware interaction, waiver, or reject/close decision.
- Rejection candidate: produce concrete research and proof. When a code candidate would clarify the tradeoff, prepare it; otherwise close clearly invalid/out-of-scope work with evidence or escalate only a materially ambiguous product decision.

The normal Bram interaction should occur only after autonomous implementation, repair, review, CI, and land/close work is exhausted. Ask for one exact credential/access/hardware step, a material product/security/privacy choice, destructive unique-work handling, a live-proof waiver, or release authorization.

When Bram asks to manually test a PR, treat that as an explicit stop-before-merge boundary. Prepare a non-draft PR with gates, live proof, confidentiality pass, and exact manual test commands, then stop without merging until Bram gives new merge authority.

## Review Gate

Run one basic review per stable candidate. Do not run a full pre-PR review and then repeat the same review before merge when the reviewed commit is still the merge candidate.

- `Basic`: every candidate, including docs, metadata, formatting, and test-only changes. Run relevant tests/checks, then default `autoreview` until no accepted/actionable findings remain.
- `Extra`: auth, secrets, privacy, external integrations, public artifact/log/screenshot/model-bearing changes, broad refactor, contributor PR rewrite, release candidate, breaking dependency, unclear behavior, or anything that failed basic review for non-trivial reasons. Add `autoreview --preset claude-opus` until clean when the extra risk justifies it or Bram asks for it. If Claude Opus is unavailable, report that the extra review is unavailable instead of treating it as routine failure.

Before merge, refresh the PR diff, CI, review state, and mergeability. Re-run the Review Gate only when candidate code, generated artifacts, public proof, or risk level changed after the last clean review. PR body edits, CI reruns, rebases with no effective diff change, or test/proof output updates do not require another review.

## Bram Decision Briefs

Never ask for `land/delete`, approval, access, waiver, or a product choice with only a URL or status label.

Immediately before asking, refresh the item and worker state. Do not repeat a question Bram already answered, and do not present an item as decision-ready when it has become conflicted, stale, red, or otherwise moved behind an autonomous repair gate.

Every Bram decision request must include:

- full canonical clickable URL and title;
- plain-language explanation of what changes and who benefits;
- why the decision is needed now;
- completed proof: reproduction, live test, tests, Review Gate result, CI, and mergeability as applicable;
- material tradeoffs, residual risks, scope concerns, or missing evidence;
- the loop's recommendation and concise rationale;
- the exact choices available and what each choice does.

When several decisions are grouped, give each item its own brief. Keep the recommendation opinionated; do not offload technical analysis to Bram. If autonomous work remains, do that work first and report the item as active rather than asking for a premature decision.

Maintain an ordered root-session Bram-question queue and ask one decision at a time. Whenever Bram answers, record and execute that answer immediately, then present the next fully prepared question in the same root session if one exists. If no Bram decision is ready, continue autonomous work and say no Bram input is currently needed; never let an answered question leave the loop idle.

When Bram defers a decision, post a concise comment on the issue or PR recording the deferral, rationale, and concrete revisit condition unless the decision is private or security-sensitive. Read existing Bram comments before asking again; never repeat a decision already recorded. Log the decision and full URL.

## Product Policy Capture

After every meaningful issue or PR decision, decide whether the rationale is a durable product rule that would prevent repeated questions. If so:

1. Read the repository's current `VISION.md` and related product docs.
2. Keep ticket-specific outcomes in the issue/PR; put only reusable product boundaries, priorities, and decision principles in `VISION.md`.
3. Own the policy judgment and exact wording in this root loop. Direct the worker to apply and validate the edit under standing repository-mutation authority, preserving checkout ownership.
4. If no `VISION.md` exists, create one only when several future decisions would benefit; do not create policy scaffolding for a one-off call.
5. Link the source issue/PR and record the policy decision in the loop log.

## Monitoring Protocol

Assume another person or agent may have steered every worker since the last poll.

Default cadence:

- newly created worker or active TDD/review/PR setup: poll every 60-120 seconds;
- queued/pending worktree setup: poll every 30-60 seconds until the worker exists or a concrete setup blocker appears;
- CI watch after PR creation: poll every 60-180 seconds until green, red, or cancelled;
- long-running but healthy worker: poll every 5 minutes after at least two coherent progress checks;
- after any worker becomes idle/completed: refresh its final answer, PR/CI state, and the repository queue before reporting.

The coordinator owns this cadence. Do not wait for Bram to type "check", "status", or "done?" before the next poll. Do not send a final answer while any delegated worker, required CI, or authorized repair loop is still active unless a precise blocker or permission boundary has been reached.

Before sending any worker message:

1. Read the worker's latest current state, including its newest user/delegation messages and active turn.
2. Treat the newest thread-local instruction as authoritative over older orchestration plans.
3. When Bram directly steers a thread or contributes work, adapt immediately: preserve and account for that work, reconcile current repository/GitHub state, and continue from Bram's direction without duplicating, undoing, or misattributing it.
4. Determine whether the worker is actively progressing, blocked, completed, or idle.
5. Send nothing when an active worker has a coherent plan and is making progress.

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

### Active Waits

- Keep the project turn active until its work reaches a terminal state. Do not emit a final answer or stop merely because CI, a runner, review, mergeability, deployment, an auth prompt, or a long command is pending.
- Prefer an in-turn 30-60 second sleep/poll cycle over a per-worker automation. After each interval, refresh the exact external state, repair or rerun when needed, and continue through landing and closeout.
- Suppress routine unchanged-poll chatter, but keep polling. The root heartbeat coordinates the repository; it does not replace a worker watching its own pending work.
- End the turn only after successful terminal closeout, one exact Bram decision/access/waiver blocker after every safe step, or a platform failure that makes continued polling impossible.

## Thread Naming

- Root sets the initial `<Project>: <current status>` title. The worker self-renames on every material transition: reviewing, implementing, proving, waiting for CI, exact blocker, ready, or complete.
- Put the project first; keep status terse, concrete, and current. Never use generic coordinate, orchestrate, or maintain labels when a specific status is known.
- Use `<Project>: done - <concrete result>` for terminal success before archiving; name the shipped or closed outcome, not merely `complete`.
- Use `waiting` only while the named external gate is verifiably pending and the worker turn remains active. The moment it succeeds, fails, or becomes irrelevant, replace the title with the next action, exact blocker, or `done`.
- Immediately before any final answer, self-rename to `<Project>: done - <concrete result>`, `<Project>: needs Bram - <exact blocker>`, or `<Project>: failed - <platform failure>`.
- Read the latest state and newest thread-local instructions before renaming.
- Keep the title specific to current work; replace stale original-task titles.
- Polling alone does not justify a rename.
- Root audits every owned title on each wake. Never leave landed, closed, released, or otherwise terminal work labeled as waiting, maintenance, reviewing, or implementing. If a title is stale, send the active worker one concise correction after reading its latest state; do not overwrite the title from a stale root snapshot. Finished or unaddressable threads are excluded from active capacity.

## Persistent Log

- This root loop owns one markdown ledger under `~/.codex/state/bram-maintainer-loop/`; workers do not edit it.
- Use one file per loop, not one global append-only file. Name it `YYYY-MM-DD-<short-loop-slug>.md`, for example `2026-06-14-current-repo.md`.
- At loop start, create or announce the ledger path. If continuing an existing loop, reuse that loop's ledger rather than starting a new file.
- Append dated, high-level entries for meaningful actions and decisions: policy/skill/automation changes, worker creation or reassignment, queue decisions, lands, closes, releases, and exact blockers.
- Include full canonical issue/PR URLs when relevant.
- Never record secrets or routine polling.
- Skip log writes when Bram explicitly requests read-only, no-edits, or dry-run behavior; report that the log append was intentionally skipped.

## Idle Thread Closeout

An idle or completed worker thread must not remain a polling-only lane. After reading its latest state, inspect the repository's current queue, CI, latest release, package metadata, docs/changelog state, and current loop priority. Then do exactly one:

1. Assign the next autonomous PR or issue to a fresh dedicated worker thread, unless reusing the exact same issue/PR worker.
2. Prepare each remaining non-autonomous item through every safe reversible step, then ask Bram only to choose a documented material alternative, provide exact access, approve destructive unique-work handling, or grant a live-proof waiver.
3. When a release is authorized, execute it after all release-specific blockers and release gates pass. Open backlog alone does not delay a release.
4. If no queue, CI, or authorized release work remains, audit and update dependencies to current stable releases. Delegate this as normal repository work: inspect upstream changes and package health, honor repository-specific stabilization policies, avoid prerelease-only upgrades unless already adopted, preserve the repository's package manager, add compatibility fixes/tests when needed, run exact built/live proof, pass the Review Gate, pass the Public Artifact Confidentiality Gate, and required CI, then land the update under standing authority.

Do not keep completed threads merely to satisfy a lane count. A monitored repository should have active autonomous work, a pending Bram question, an active release, or a documented reason no release is warranted.

Dependency freshness is a backstop, not higher priority than real queue, CI, or release work.

Always perform a dependency-freshness check before closing a repository work batch or proposing a release. Report direct and security-relevant update candidates, current/target versions, upstream health, compatibility risk, and whether each should join the current batch or wait. Do not silently skip the check because queue work existed.

Architecture review is a backstop and recommendation lane, not an automatic worker step. When repeated workers report hard-to-test modules, shallow modules, unclear seams, or cross-cutting refactor pressure, report `improve-codebase-architecture` as `Ready next` for Bram to invoke separately. Do not run it inside the loop unless Bram explicitly asks for an architecture pass.

## Authorization

Bram grants standing autonomous authority for in-scope current-repository queue work coordinated by this session. Worker threads may synchronize clean checkouts; edit; create branches; commit; push; open or update PRs; write proof/review/close comments; approve, rerun, and repair CI; merge supported exact-head green changes; close resolved or invalid items; and return to synchronized clean `main`. Do not request per-item permission to implement, repair, improve, rewrite, publish a PR, fix CI, or land clearly supported work.

This standing authority does not include:

- releases, version bumps, tags, registry publishing, or GitHub Releases;
- destructive handling of unique local work or user data;
- material product, security, privacy, legal, credential-sharing, or irreversible choices that lack a safe reversible default;
- external-system mutations beyond the repository/GitHub workflow unless separately authorized.

Read-only, no-edits, dry-run, plan-only, or audit-only overrides all mutation permission: no local edits, fetches, pulls, branch checkout, commits, pushes, PR/issue comments or creation, CI reruns, worker thread creation/renames, heartbeat changes, or loop log writes. Report findings, proposed branch/PR plan, and the exact next permission needed.

When Bram asks to manually test a PR, stop before merge even if ordinary loop authority would allow landing. Resume landing only after Bram gives new merge authority.

Clearly qualifying noise retains standing silent-close authority. A newer Bram instruction may narrow any project. Record standing authority and exceptions in every worker prompt; stop only at the exact remaining exception or hard blocker.

`ship` uses repo `AGENTS.MD` meaning: changelog, commit in groups, push, pull.

`fix ci` authorizes pull, commit, push, rerun/watch until green for that CI task.

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

Every delegated implementation thread, under standing authority and any newer project-specific limits, must:

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
- commit and push the final candidate, then open or update its PR;
- rerun required checks and repair failures until exact-head CI is green;
- remain active through CI/review/deployment waits using bounded sleep/poll cycles; never stop at a nonterminal waiting status;
- merge or close the queue item with exact proof when evidence supports it;
- after landing, return to updated, clean `main`;
- update the changelog for user-visible changes; within the active unreleased/release section, order entries from most to least interesting to users and keep the repository's established format;
- after the assigned queue work, audit dependency freshness and report actionable updates even when none are taken;
- report every candidate and completed change with full clickable URLs, files changed, insertions, deletions, low/medium/high risk with rationale, proof state, and recommendation;
- ask repository-specific questions only in this worker thread.

Prefer repairing the contributor PR. Preserve contributor credit and follow the workspace PR rules.

If a newer project-specific instruction narrows standing authority, stop at that boundary after completing every still-authorized step and state the exact remaining action.

## Live Proof Gate

Live proof is a pre-land requirement for runtime behavior, not optional polish.

- Test the exact final candidate commit through the changed user path using the real built/installed artifact and real service, account, device, OS, or external provider as applicable.
- For external integrations, authenticated live calls are required when credentials are available. Docs, mocks, fixtures, protocol captures, route-existence checks, and CI supplement live proof; they do not replace it.
- Redact secrets and private user data while retaining concrete evidence such as command, behavior, response class, artifact hash, or observed state transition.
- If credentials, account state, hardware, platform access, or a safe live target are unavailable, finish all autonomous code, tests, review, and CI work, then stop before merge/close. Ask for the exact access, an explicit item-specific waiver, or a reject/close decision.
- Never infer a live-proof waiver from merge permission, release permission, prior contributor evidence, or confidence in mocks.
- Re-run live proof after any fix that changes the relevant runtime path.
- Pure docs, metadata, CI, or test-only changes with no runtime boundary may use the closest built-artifact or workflow proof; state why no external live boundary applies.
- When UI screenshot proof is requested, capture the actual running UI surface being changed: app window, native menu, status item, browser viewport, or equivalent. Do not substitute generated artifacts, SVG renders, diagrams, fixture cards, or model-only proof unless Bram explicitly accepts that waiver.
- Public UI proof must render where reviewers will read it. Prefer GitHub `user-attachments`/`gh image` or another verified inline-rendering path; do not call raw branch links, local paths, private raw URLs, or unrendered generated files sufficient proof.

Record live evidence or Bram's explicit waiver in the landing proof comment.

## Public Artifact Confidentiality Gate

Before any push, public PR update, merge, or release involving secrets, model identifiers, private endpoints, personal data, generated logs, screenshots, packaged artifacts, or public proof:

- Audit the exact candidate diff, tests, fixtures, snapshots, generated metadata, workflows, CI/test logs, packaged artifacts, and public PR/issue proof.
- Do not expose non-public organizational information, credentials, URLs, datasets, personnel details, internal model names, or proprietary context.
- For model-bearing code or artifacts, audit specifically for model identifiers.
- Public model identifiers may remain only when they are currently documented or offered in an official public provider source. Record the source URL in the worker's audit report.
- Never expose internal, employee-only, preview-only, alias-only, inferred, synthetic provider-shaped, or otherwise undisclosed identifiers. Genericize questionable test and fixture values because assertion failures can print them in CI logs.
- Do not repeat questionable secret-like, internal, or unverified model identifier strings in worker messages, audit reports, public comments, or the loop log. Describe them generically.
- Binary/archive scans must classify candidate strings as verified public identifiers, unrelated false positives, or blocking unknowns without echoing blocking unknowns.
- Return an explicit `PASS` or `BLOCKED` report covering every audited surface. Any new candidate diff, generated artifact, log/proof text, or model-bearing change invalidates the pass and requires re-audit.

No push, public mutation, merge, or release may proceed while this gate is blocked.

## Release Proposals

Propose a release when either all effective repository tasks are complete or a meaningful user-visible batch has accumulated. Judge meaningfulness by user impact and coherence, not a fixed item count. Do not wait for a perfectly empty queue when a coherent release is already valuable; unrelated backlog does not block a release.

Every proposal must include:

- recommended version and SemVer rationale;
- `Highlights`: two to five most valuable user outcomes, strongest first;
- full ordered changelog, most to least interesting to users, with full issue/PR URLs;
- dependency-freshness result and any update deliberately deferred;
- exact-head CI, tests, live proof, artifacts, and release-gate state;
- remaining backlog, actual release-specific blockers, residual risk, and one exact release/hold choice.

Match repository changelog style. For a meaningful release, add or maintain a `Highlights` subsection in the target changelog section when compatible; otherwise lead the target section with the highlight bullets before the full ordered entries. Do not reorder historical released sections. A proposal never authorizes version bumps, tags, publishing, GitHub Releases, or pushes.

## Release Gate

Open issues and PRs are backlog inventory, not release blockers by default. Compute only the candidate-specific blocker set immediately before release:

```text
release blockers = items explicitly scoped to the target release
                 + active authorized work promised for the target release
                 + demonstrated regressions affecting the release candidate
```

Do not ask Bram to exempt unrelated open issues or PRs. An item blocks only when repository metadata, Bram instruction, the release plan, or concrete validation ties it to the target release. Security exposure, data loss, broken install/upgrade, and candidate regressions block when they affect the candidate even without a milestone or label.

Release only when all are true:

- Bram explicitly requested this release or authorized release execution for the repository;
- release-specific blocker count is zero;
- required CI is green for the exact commit and branch/tag candidate being released;
- all user-facing runtime changes in the release have required live proof, unless Bram explicitly waives that proof for the release;
- release checkout is clean, on the expected branch, and fast-forward current;
- unreleased changes justify a release and the target version follows SemVer/project convention.

Recheck release-specific blockers, the candidate diff, and CI immediately before tagging or publishing. Abort if any gate changes.

In release reporting, list actual release blockers reviewed and their resolution. Do not enumerate or request waivers for unrelated backlog.

## Release Execution

Use the repository's release docs and matching skill:

- npm packages: use `npm`;
- macOS apps: use repo release docs and any matching release skill;
- other projects: use established repo scripts/workflows.

If release docs, changelog, tags, or CI/release workflows are missing, do not infer a release path. Report the missing release lane and prepare docs/workflow improvements only when authorized.

Before release:

- reconcile changelog history with existing tags/releases;
- ensure the target changelog section starts with the strongest user-facing highlights and orders remaining entries from most to least interesting;
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

Keep one compact current-repo ledger:

- `Active`: item URL, worker, current phase.
- `Intervened`: exact risk and instruction sent.
- `Needs Bram`: exact decision/access required; no vague "needs review".
- `Ignored`: exact item and Bram-granted exception.
- `Vision`: durable product rule proposed or updated, with source item URL.
- `Dependencies`: actionable updates or explicit current/no-update result.
- `Release proposed`: version, highlights, ordered changelog, gates, risk, and exact release/hold choice.
- `Released`: version, tag/registry verification, closeout commit.
- `Ready next`: release-specific blockers clear, CI green, recommended patch/minor version and rationale.

For each active, decision-ready, or landed code change, include `files / +insertions / -deletions` and a low/medium/high risk estimate with one-line rationale. Summaries must be self-contained; never assume Bram opened the linked issue, PR, or worker thread.

Omit archived and Bram-suppressed repositories entirely. Do not list them as ignored, blocked, stale, or available work.

Whenever mentioning an issue or PR in any report, decision question, worker message, or status update, print its full canonical clickable URL. Never use only a repository-local number such as `#123`; include `https://github.com/OWNER/REPO/issues/123` or `https://github.com/OWNER/REPO/pull/123`.

For `Needs Bram`, use the Bram Decision Brief format. Never emit a bare URL plus `land/delete`.

Report meaningful changes, not routine polling. Use the Activation Watch rules for heartbeat automation.
