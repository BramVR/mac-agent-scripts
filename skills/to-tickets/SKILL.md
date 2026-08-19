---
name: to-tickets
description: "Break a plan, spec, or conversation into tracer-bullet tickets with blocking edges and required proof, then publish them to the configured issue tracker."
disable-model-invocation: true
---

# To Tickets

_Source: [mattpocock/skills](https://github.com/mattpocock/skills), synced from `main` at `885e2ca4`; extended with Bram's AFK/HITL and automatic live-proof rules._

Break a plan, spec, or conversation into **tickets**: tracer-bullet vertical slices, each declaring the tickets that block it.

The issue tracker and triage label vocabulary should have been configured. If not, tell the user to run `/setup-matt-pocock-skills`.

## Process

### 1. Gather context

Work from the conversation context. If the user passes a spec path, issue number, URL, or other reference, fetch it and read its full body and comments.

### 2. Explore the codebase when needed

Explore enough code to understand the current state. Ticket titles and descriptions should use the project's domain glossary vocabulary and respect relevant ADRs.

Look for prefactoring that would make implementation easier. Make the change easy, then make the easy change.

### 3. Draft vertical slices

Break the work into tracer-bullet tickets.

<vertical-slice-rules>

- Each slice cuts a narrow but complete path through every relevant layer, such as schema, API, UI, and tests. Do not create horizontal layer tickets.
- A completed slice is demoable or verifiable on its own.
- Each slice fits in one fresh context window.
- Put required prefactoring first.

</vertical-slice-rules>

Give each ticket its **blocking edges**, meaning the tickets that must complete before it can start. A ticket with no blockers can start immediately.

Classify each ticket:

- **AFK** when an agent can implement, prove, review, and land it without user interaction.
- **HITL** when it needs a user decision, manual approval, unavailable credential, live environment setup, or another non-automatable action.

Prefer AFK. Do not label a ticket AFK when its proof still requires Bram.

**Wide refactors are the exception to vertical slicing.** A wide refactor is one mechanical change, such as renaming a column or retyping a shared symbol, whose blast radius prevents one vertical slice from landing green. Sequence it as expand-contract:

1. Expand by adding the new form beside the old.
2. Migrate callers in batches sized by blast radius, each blocked by the expansion.
3. Contract by deleting the old form after every migration batch.

If individual migration batches cannot stay green, use an integration branch and make them block one final integrate-and-verify ticket.

### 3b. Require real proof when reality is the product

If behavior matters only against a real dependency, require an automatic real proof gate. Fake or local tests still prove the machinery, but they do not close the ticket.

Real dependencies include live hosts, browsers, devices, external CLIs, OAuth-backed services, payment providers, review systems, deployment targets, hardware, licensed desktop apps, and consuming repositories.

<real-proof-rules>

- Acceptance criteria name the exact real proof command, workflow, smoke test, or CI job.
- The real proof runs automatically once configured. No manual Bram step may remain in an AFK ticket.
- A skipped, missing, or fake-only real proof fails the ticket.
- Mark the ticket HITL unless the required credentials, host, and configuration already exist in automation.
- If automatic real proof does not exist, create one HITL ticket to establish the proof gate. Block AFK implementation tickets on it.
- If live proof changes the supported product promise, include the related docs, ADR, or spec cleanup in the same slice.

</real-proof-rules>

### 4. Quiz the user

Present the proposed breakdown as a numbered list. For each ticket, show:

- **Title**: short descriptive name.
- **Type**: AFK or HITL.
- **Blocked by**: tickets that genuinely gate it.
- **What it delivers**: end-to-end behavior that becomes usable.
- **User stories**: covered stories when the source includes them.
- **Real proof**: the automatic live gate, or "not needed" with a reason.

Ask whether the granularity, blocking edges, AFK or HITL labels, and real proof gates are correct. Iterate until the user approves the breakdown.

### 5. Publish to the configured tracker

Publish approved tickets in dependency order so blockers get identifiers first.

- **Local files**: write one file per ticket under `.scratch/<feature-slug>/issues/<NN>-<slug>.md`, numbered from `01`. Never combine tickets into one file.
- **A real tracker**: publish one issue per ticket. Use native blocking or sub-issue relationships where available, otherwise write the blocking references in the body. Apply the `ready-for-agent` label to AFK tickets unless instructed otherwise.

Do not close or modify a parent issue.

<local-ticket-template>

# <NN>: <Ticket title>

**Type:** AFK or HITL

**What to build:** the end-to-end behavior this ticket makes work from the user's perspective.

**Blocked by:** ticket numbers and titles, or "None (can start immediately)".

**Status:** ready-for-agent or ready-for-human

## Acceptance criteria

- [ ] Criterion 1
- [ ] Criterion 2

## Required proof

- Fake or local gate: exact command.
- Real gate: exact automatic live command, workflow, smoke test, or CI job, or "Not required" with the reason.
- Merge rule: a skipped or fake-only required real gate means the ticket is incomplete.

</local-ticket-template>

<issue-template>

## Parent

Reference the parent issue when the source was an existing issue. Otherwise omit this section.

## Type

AFK or HITL.

## What to build

Describe the end-to-end behavior, not a layer-by-layer implementation list.

## Acceptance criteria

- [ ] Criterion 1
- [ ] Criterion 2

## Required proof

- Fake or local gate: exact command.
- Real gate: exact automatic live command, workflow, smoke test, or CI job, or "Not required" with the reason.
- Merge rule: a skipped or fake-only required real gate means the ticket is incomplete.

## Blocked by

Reference every blocking ticket, or write "None (can start immediately)".

</issue-template>

Avoid specific file paths or code snippets because they go stale. If a prototype produced a decision-rich state machine, reducer, schema, or type shape, include only the part that records the decision and note that it came from the prototype.
