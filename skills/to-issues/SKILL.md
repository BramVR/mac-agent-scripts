---
name: to-issues
description: Break a plan, spec, or PRD into independently-grabbable issues on the project issue tracker using tracer-bullet vertical slices. Use when user wants to convert a plan into issues, create implementation tickets, or break down work into issues.
---

# To Issues

Break a plan into independently-grabbable issues using vertical slices (tracer bullets).

If tracker labels are unknown, inspect repo labels with `gh label list` or ask Bram only when publishing requires a decision.

## Process

### 1. Gather context

Work from whatever is already in the conversation context. If the user passes an issue reference (issue number, URL, or path) as an argument, fetch it from the issue tracker and read its full body and comments.

### 2. Explore the codebase (optional)

If you have not already explored the codebase, do so to understand the current state of the code. Issue titles and descriptions should use the project's domain glossary vocabulary, and respect ADRs in the area you're touching.

### 3. Draft vertical slices

Break the plan into **tracer bullet** issues. Each issue is a thin vertical slice that cuts through ALL integration layers end-to-end, NOT a horizontal slice of one layer.

Slices may be 'HITL' or 'AFK'. HITL slices require human interaction, such as an architectural decision or a design review. AFK slices can be implemented and merged without human interaction. Prefer AFK over HITL where possible.

Loop mode: in `bram-maintainer-loop-v2`, draft the slices and AFK/HITL labels as the decision boundary. Publish issues only when issue creation is authorized.

<vertical-slice-rules>
- Each slice delivers a narrow but COMPLETE path through every layer (schema, API, UI, tests)
- A completed slice is demoable or verifiable on its own
- Prefer many thin slices over few thick ones
</vertical-slice-rules>

### 3b. Require real proof when reality is the product

If the slice changes behavior that only matters against a real dependency, the issue must require an automatic real proof gate. Fake/default tests are still required for machinery, but they are not enough to close or merge real behavior.

Examples of real dependencies: live hosts, browsers, devices, external CLIs, OAuth-backed services, payment providers, review systems, deployment targets, hardware, licensed desktop apps, or consuming repos.

<real-proof-rules>
- Acceptance criteria must name the real proof command, workflow, smoke, or CI job.
- The real proof must be automatic once configured; no manual Bram step may be required during merge.
- A skipped, missing, or fake-only real proof fails the issue.
- Mark the slice HITL unless the required live credentials/host/config already exist in automation and the agent can verify them without asking.
- If real proof is impossible, split first: one HITL slice to create the automated proof gate, then AFK implementation slices blocked by it.
- If the product promise changes because real proof shows a feature is unsupported, include docs/ADR/PRD cleanup in the same vertical slice.
</real-proof-rules>

### 4. Quiz the user

Present the proposed breakdown as a numbered list. For each slice, show:

- **Title**: short descriptive name
- **Type**: HITL / AFK
- **Blocked by**: which other slices (if any) must complete first
- **User stories covered**: which user stories this addresses (if the source material has them)
- **Real proof**: automatic live gate required, or "not needed" with a reason

Ask the user:

- Does the granularity feel right? (too coarse / too fine)
- Are the dependency relationships correct?
- Should any slices be merged or split further?
- Are the correct slices marked as HITL and AFK?
- Does every real-product slice have a non-skippable automatic proof gate?

Iterate until the user approves the breakdown.

### 5. Publish the issues to the issue tracker

For each approved slice, publish a new issue to the issue tracker. Use the issue body template below. These issues are considered ready for AFK agents, so publish them with the correct triage label unless instructed otherwise.

Publish issues in dependency order (blockers first) so you can reference real issue identifiers in the "Blocked by" field.

<issue-template>
## Parent

A reference to the parent issue on the issue tracker (if the source was an existing issue, otherwise omit this section).

## What to build

A concise description of this vertical slice. Describe the end-to-end behavior, not layer-by-layer implementation.

Avoid specific file paths or code snippets — they go stale fast. Exception: if a prototype produced a snippet that encodes a decision more precisely than prose can (state machine, reducer, schema, type shape), inline it here and note briefly that it came from a prototype. Trim to the decision-rich parts — not a working demo, just the important bits.

## Acceptance criteria

- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

## Required proof

- Fake/local gate: exact command(s) that must pass.
- Real gate: exact automatic live command, workflow, smoke, or CI job that must pass; or "Not required" with the reason.
- Merge rule: if a required real gate is skipped, missing, or replaced by fake-only proof, this issue is not complete.

## Blocked by

- A reference to the blocking ticket (if any)

Or "None - can start immediately" if no blockers.

</issue-template>

Do NOT close or modify any parent issue.
