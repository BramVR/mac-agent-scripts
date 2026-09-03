---
name: reflect
description: Spawn three parallel review subagents over the active transcript, surface learnings, and route each to a concrete edit on an existing skill. Use when the user says reflect.
---

# Reflect

Mine the current conversation for durable learnings, then route them into skill edits.

## When to invoke

- The user said "reflect" or "$reflect".
- A complex task (5+ tool calls) just landed cleanly and the recipe is worth keeping.
- The agent hit dead ends, found the working path, and the path generalizes.
- The user corrected the agent's approach mid-task.
- A non-trivial workflow emerged that isn't captured anywhere.

Skip when the conversation is trivial, off-topic, or already covered by an existing skill the parent followed correctly. One-offs are not learnings.

## Process

### 1. Locate the active transcript

The parent finds its own transcript file before fanning out. Use the exact ID from `CODEX_THREAD_ID` or `CODEX_SESSION_ID` to locate the matching rollout under `${CODEX_HOME:-$HOME/.codex}/sessions/`. Do not scan unrelated rollout files. That crosses workspace boundaries and reads private chats from unrelated projects.

```bash
thread_id="${CODEX_THREAD_ID:-$CODEX_SESSION_ID}"
find "${CODEX_HOME:-$HOME/.codex}/sessions" -type f -name "rollout-*-${thread_id}.jsonl" -print -quit
```

Codex rollout layout: `<sessions>/YYYY/MM/DD/rollout-<timestamp>-<thread-id>.jsonl`.

Read the earliest `response_item` whose payload is a user message and check that its text contains the conversation's opening user prompt. Take the matching path. If no path resolves, write a tight digest of the session and pass that instead.

### 2. Spawn three reviewers in parallel

One message, three Codex collaboration-agent calls. Each uses its assigned model below with `reasoning_effort: "high"` and `fork_turns: "none"`. Use standard mode; never use fast mode or substitute another model or reasoning level. Reviewers need tool access for context lookups (tickets, chat threads, observability traces referenced in the transcript). Codex does not expose a read-only switch for collaboration agents; the prompt forbids file writes and the parent applies edits.

| Lens | `model` | Prompt template |
|---|---|---|
| Judgment | `gpt-5.6-sol` at `high` reasoning | `references/judgment-reviewer.md` |
| Tooling | `gpt-5.6-luna` at `high` reasoning | `references/tooling-reviewer.md` |
| Divergent | `gpt-5.6-terra` at `high` reasoning | `references/divergent-reviewer.md` |

Pass each template verbatim, substituting the transcript path or digest where marked. Reviewers return findings in their final response.

### 3. Synthesize

One Codex collaboration-agent call with `model: "gpt-5.6-sol"`, `reasoning_effort: "high"`, and `fork_turns: "none"`. Use standard mode; never use fast mode. The synthesizer's quality check includes spot-verifying citations, which can require tool access. Codex does not expose a read-only switch for collaboration agents; the prompt forbids file writes and the parent applies edits. Use `references/synthesizer.md` verbatim, with each reviewer's full output inlined where marked. The synthesizer returns a structured Accepted / Rejected / Backlog list.

### 4. Structural enforcement check

Sanity-check the synthesizer's Accepted list. For any item that would be enforced more reliably by a lint rule, script, metadata flag, or runtime check, move it from Accepted to Backlog. The synthesizer already applies this criterion; this is a final pass before edits land. See the **encode-lessons-in-structure** principle skill.

### 5. Apply

Before applying any Accepted edit, present the synthesizer's full Accepted/Rejected/Backlog output to the user and wait for explicit approval. The user picks which subset to apply and may redirect routings. Skill changes affect every future agent in the org; do not auto-apply.

Backlog items file to whatever devex / backlog tracker your team uses automatically when the user has already authorized external writes. Otherwise report them as ready to file. Those are tracker submissions, not skill edits. Only the Accepted list waits for approval.

For each approved Accepted item, follow the Routing field exactly:

- Trivial existing-skill edit (a one-line bullet, a tightened sentence, a stale fact corrected): parent does directly.
- Substantive existing-skill edit (a new section, a new pattern table, more than ~10 lines): hand to Codex's built-in `$skill-creator` skill and run its draft / test / iterate loop.
- `tune description: <skill path>` (the skill exists but didn't trigger when it should have): hand to `$skill-creator` and run its description-optimization loop.
- `new skill via skill-creator: <kebab-name>`: hand creation to `$skill-creator`. Do not invent the shape ad hoc.

If your environment ships a SKILL.md validator, run it on every touched skill before declaring done. Skip this step if it doesn't.

### 6. Summarize for the user

Short list, no preamble:

- Edits applied: `<skill path>`. What changed, one line each.
- New skills created: `<skill path>`. One line each (rare).
- Backlog filed to the devex tracker: `<issue title>` (`<tags>`). One line each.
- Dropped: one line per rejected finding + reason from the synthesizer.
