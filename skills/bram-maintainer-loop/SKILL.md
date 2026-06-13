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
- Initial flagged repos: `gohealthcli`, `gobankcli`.
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
3. When delegation is explicitly authorized, this root loop session delegates independent repositories to separate Codex threads. Whenever assigning or materially changing work, rename the worker thread to `<Project>: <short current task>`. Keep work for one repository in its existing thread. Do not set or request a custom model; omit model selection and inherit the platform default.
4. Keep this coordinator thread lightweight. Do not perform extensive repository work here. Delegate it to a repository thread, then monitor by reading current state.
5. Monitor workers every five minutes when Bram requests continuous orchestration. Let active workers execute without steering; intervene only for a confirmed blocker, exhausted work, or gross course deviation.
6. Continue until each autonomous item is merged/closed with proof, each decision item has a mergeable PR ready for Bram's land/delete/access choice, an empty effective queue has either an explicitly authorized gated release completed or a documented no-release/needs-authorization reason, or an otherwise idle repository has current dependencies/docs.

Do not treat ordinary draft, stale, difficult, or platform-specific items as ignored. Only an explicit Bram instruction can create an ignored-item exception. Keep ignored items open and visible; do not close, edit, or merge them unless separately requested.

## Flagged Repo List

Read `~/Projects/agent-scripts/config/bram-loop-repos.txt` for broad loops. One repo slug per line. Blank lines and `#` comments are ignored.

Recommended initial loop:

```text
gohealthcli
gobankcli
```

When Bram asks to add or remove loop repos, edit that config and keep the change terse.

## Control-Plane Ownership

- Only this root loop session may create, reuse, fork, assign, rename, archive, or steer worker threads.
- Repository workers perform only their assigned repository work and report results to this loop. They must not create subworkers, delegate work, or manage other chats.
- Put the no-subdelegation rule in every worker prompt.
- Do not delegate portfolio triage, thread creation, or worker management to another worker.
- Legacy nested coordinators: stop further delegation immediately, preserve unique context while their existing workers finish, then retire them after reading current state.

## Decision-Ready Queue Rule

Do not ask Bram to decide from an unprepared issue or rough contributor branch.

- Existing PR: inspect, reproduce, rewrite/fix as needed, add tests/docs/changelog when appropriate, run live proof and `autoreview`, push the final candidate only when authorized, and get required CI green when CI work is authorized. Ask only when the PR is mergeable or the remaining blocker cannot be solved autonomously.
- Issue without PR: investigate root cause and product constraints, use `tdd` for implementation when code behavior changes, create a PR only when authorized, and drive it to the same mergeable proof state.
- Vague feature/product idea: use `to-prd` or `to-issues` before implementation when the request is too broad for one autonomous slice.
- Product decision: choose a reversible default when technically safe and expose the decision clearly in the PR or report. Prepare alternatives when useful.
- Access or live-proof blocker: finish code, tests, docs, review, and CI first. Ask only for the exact remaining credential, account action, hardware interaction, waiver, or land/delete decision.
- Rejection candidate: produce concrete research and proof. When a code candidate would clarify the tradeoff, prepare the PR anyway; otherwise update the issue/report with the evidence needed for a Bram close/keep decision.

The normal Bram interaction should be one of: land the prepared PR, delete/close it, provide one exact access step, grant one explicit waiver, or choose between clearly documented alternatives.

## Owner Decision Briefs

Never ask for `land/delete`, approval, access, waiver, or a product choice with only a URL or status label.

Immediately before asking, refresh the item and worker state. Do not repeat a question Bram already answered, and do not present an item as decision-ready when it has become conflicted, stale, red, or otherwise moved behind an autonomous repair gate.

Every decision request must include:

- full canonical clickable URL and title when the item exists on GitHub;
- plain-language explanation of what changes and who benefits;
- why the decision is needed now;
- completed proof: reproduction, live test, tests, `autoreview`, CI, and mergeability as applicable;
- material tradeoffs, residual risks, scope concerns, or missing evidence;
- the loop's recommendation and concise rationale;
- the exact choices available and what each choice does.

When several decisions are grouped, give each item its own brief. Keep the recommendation opinionated; do not offload technical analysis to Bram. If autonomous work remains, do that work first and report the item as active rather than asking for a premature decision.

## Monitoring Protocol

Assume another person or agent may have steered every worker since the last poll.

Before sending any worker message:

1. Read the worker's latest current state, including newest user/delegation messages and active turn.
2. Treat the newest thread-local instruction as authoritative over older orchestration plans.
3. Determine whether the worker is actively progressing, blocked, completed, or idle.
4. Send nothing when an active worker has a coherent plan and is making progress.

Intervene only when evidence shows one of:

- the worker explicitly requests coordination or reports a blocker;
- the worker has completed or run out of autonomous work and needs a next queue item;
- repeated failures show no progress and a concrete correction is available;
- wrong repository/item, unauthorized mutation, destructive action, security risk, release-gate violation, or direct conflict with Bram's latest instruction;
- implementation has grossly diverged from the accepted task, not merely chosen a different reasonable design.

Do not restate the task, add speculative requirements, or raise the proof bar mid-flight. Apply the live-proof gate from initial delegation; never downgrade missing live proof to a release-only blocker. Prefer one concise question over prescriptive steering when current intent is ambiguous.

Never interrupt, archive, rename, duplicate, or replace a worker without first reading its current state. For a suspected duplicate, read both threads; if either has unique progress, edits, or an active turn, leave it alone and ask Bram before changing thread state.

## Thread Naming

- Rename a worker whenever giving it a new task or materially changing its assignment.
- Format every worker title as `<Project>: <short current task>`.
- Read the latest state and newest thread-local instructions before renaming.
- Keep the title specific to current work; replace stale original-task titles.
- Polling alone does not justify a rename.

## Persistent Log

- This root loop owns `~/.codex/state/bram-maintainer-loop.md`; workers do not edit it.
- Append dated, high-level entries for meaningful actions and decisions: policy/skill changes, worker creation or reassignment, queue decisions, lands, closes, releases, and exact blockers.
- Include full canonical issue/PR URLs when relevant.
- Never record secrets or routine polling.
- Skip log writes when Bram explicitly requests read-only, no-edits, or dry-run behavior; report that the log append was intentionally skipped.

## Idle Thread Closeout

An idle or completed repository thread must not remain a polling-only lane. After reading its latest state, inspect that repository's current queue, CI, latest release, package metadata, docs/changelog state, and flagged repo priority. Then do exactly one:

1. Assign the next autonomous issue or PR to the same repository thread.
2. Prepare each remaining non-autonomous item to the decision-ready boundary, then ask Bram a concise concrete question.
3. When the effective issue and PR queues are empty, execute the authorized patch or minor release after all release gates pass.
4. If no queue, CI, or authorized release work remains, treat dependency freshness as the next candidate backstop. When implementation is authorized, or when delegation is separately authorized, audit and update dependencies to compatible current stable releases unless Bram authorizes breaking-major upgrades. Delegate this as normal repository work: inspect upstream changes and package health, honor repository-specific stabilization policies, avoid prerelease-only upgrades unless already adopted, preserve the repository's package manager, add compatibility fixes/tests when needed, run exact built/live proof, `autoreview`, the Public Artifact Confidentiality Gate, and required CI, then prepare or land the update within granted permissions. Without implementation/delegation authorization, report dependency freshness as the next candidate work and stop.

Do not keep completed threads merely to satisfy a lane count. A monitored repository should have active autonomous work, a pending Bram question, an active release, or a documented no-release/needs-authorization reason.

Dependency freshness is a backstop, not higher priority than real queue, CI, or release work.

## Authorization

Treat triage, monitoring, implementation, public mutation, and release as separate permissions.

- Queue analysis or monitoring does not authorize edits.
- Delegation or parallel-worker creation requires explicit Bram authorization.
- Implementation permission authorizes local changes and verification only unless Bram also authorizes push/PR updates.
- Push permission does not imply merge or close permission.
- CI rerun and CI-fix permission must be explicit; a push alone does not authorize additional repair commits or workflow mutations.
- Merge/close permission must be explicit for the affected work.
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

- read the full issue/PR discussion, repo instructions, docs, and relevant code;
- when work is broad or vague, use `to-prd` or `to-issues` before implementation;
- when changing code behavior, use `tdd` unless the change is too trivial or docs-only;
- reproduce or establish root cause before accepting an existing patch;
- rewrite when a cleaner bounded design is available;
- add regression coverage when appropriate;
- run focused and full tests, then live/end-to-end proof against the real affected boundary before landing;
- run `autoreview` until no accepted/actionable findings remain;
- when push is authorized, push the authorized changes;
- when CI rerun/fix is authorized, rerun required checks and repair failures until green;
- when CI rerun/fix is not authorized and checks fail, stop with the exact failure and requested permission;
- when merge/close is authorized, merge or close the queue item with an exact proof comment;
- after authorized landing, return to updated, clean `main`.

Prefer repairing contributor PRs when writable. Preserve contributor credit and follow workspace PR rules.
When landing is not yet authorized, stop only after the branch is pushed if push is authorized, the PR is mergeable, required CI is green, live proof is recorded, and the exact Bram decision is stated.

## Live Proof Gate

Live proof is a pre-land requirement for runtime behavior, not optional polish.

- Test the exact final candidate commit through the changed user path using the real built/installed artifact and real service, account, device, OS, or external provider as applicable.
- For external integrations, authenticated live calls are required when credentials are available. Docs, mocks, fixtures, protocol captures, route-existence checks, and CI supplement live proof; they do not replace it.
- Redact secrets and private user data while retaining concrete evidence such as command, behavior, response class, artifact hash, or observed state transition.
- If credentials, account state, hardware, platform access, or a safe live target are unavailable, finish all autonomous code, tests, review, and CI work, then stop before merge/close. Ask for the exact access, an explicit item-specific waiver, or a reject/close decision.
- Never infer a live-proof waiver from merge permission, release permission, prior contributor evidence, or confidence in mocks.
- Re-run live proof after any fix that changes the relevant runtime path.
- Pure docs, metadata, CI, or test-only changes with no runtime boundary may use the closest built-artifact or workflow proof; state why no external live boundary applies.

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
- run full release checks and review release-only edits.

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
