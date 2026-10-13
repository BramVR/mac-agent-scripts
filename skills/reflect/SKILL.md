---
name: reflect
description: "Spawn three parallel review subagents over the active transcript, surface learnings, and route each to a concrete edit on an existing skill. Use when the user says reflect."
---

# Reflect

Mine the current conversation for durable learnings, then route them into skill edits.

Invoke when the user says "reflect" or "$reflect". Skip when the conversation is trivial, off-topic, or already covered by an existing skill the parent followed correctly. One-offs are not learnings.

## 1. Locate the active transcript

Before fanning out, find this conversation's transcript using the exact ID from `CODEX_THREAD_ID` or `CODEX_SESSION_ID` under `${CODEX_HOME:-$HOME/.codex}/sessions`. Do not read other rollouts. That crosses project boundaries and reads private chats from unrelated work.

```bash
thread_id=${CODEX_THREAD_ID:-${CODEX_SESSION_ID:-}}
if [ -n "$thread_id" ]; then
  find "${CODEX_HOME:-$HOME/.codex}/sessions" -type f -name "rollout-*-${thread_id}.jsonl" -print -quit
fi
```

Codex rollout layout: `<sessions>/YYYY/MM/DD/rollout-<timestamp>-<thread-id>.jsonl`. Read the matching rollout's `response_item` records with `payload.type: message` and `payload.role: user`; their `input_text` content holds the user prompts. The first JSONL record is session metadata, not a user message. Confirm the opening user prompt belongs to this conversation. If the ID or matching rollout is unavailable, pass a tight digest of the session instead.

## 2. Spawn three reviewers in parallel

Spawn three Codex collaboration agents concurrently, with explicit `model` and `reasoning_effort` on each. Reviewers need MCP access to look up the tickets, chat threads, and observability traces the transcript references.

| Lens | `model` | Prompt template |
|---|---|---|
| Judgment | your configured `reflect judgment` model from `${CODEX_HOME:-$HOME/.codex}/skills/poteto-mode/references/models.md` (default `gpt-6.1-sol` at `high` reasoning) | `references/judgment-reviewer.md` |
| Tooling | your configured `reflect tooling` model from `${CODEX_HOME:-$HOME/.codex}/skills/poteto-mode/references/models.md` (default `gpt-6.1-sol` at `high` reasoning) | `references/tooling-reviewer.md` |
| Divergent | your configured `reflect judgment` model from `${CODEX_HOME:-$HOME/.codex}/skills/poteto-mode/references/models.md` (default `gpt-6.1-sol` at `high` reasoning) | `references/divergent-reviewer.md` |

Pass each template verbatim, substituting the transcript path or digest where marked. Reviewers return findings in the agent response body.

## 3. Synthesize

One agent call, using your configured `reflect judgment` model from `${CODEX_HOME:-$HOME/.codex}/skills/poteto-mode/references/models.md` (default `gpt-6.1-sol` at `high` reasoning). Pass the effort as `reasoning_effort`. It spot-verifies citations through MCP. Pass `references/synthesizer.md` verbatim, with each reviewer's full output inlined where marked. It returns an Accepted / Rejected / Backlog list.

## 4. Structural enforcement check

Move any Accepted item that a lint rule, script, metadata flag, or runtime check would enforce more reliably to Backlog. See the **encode-lessons-in-structure** principle skill.

## 5. Apply

Present the synthesizer's full Accepted / Rejected / Backlog output and wait for explicit approval before applying any Accepted edit. The user picks the subset and may redirect routings. Skill changes affect every future agent in the org. Do not auto-apply.

File each Backlog item to your team's devex or backlog tracker without waiting. Only the Accepted list waits for approval.

Follow each approved row's Routing exactly:

- Trivial existing-skill edit (a one-line bullet, a tightened sentence, a stale fact corrected): the parent does it directly.
- Substantive existing-skill edit (a new section, a new pattern table, more than ~10 lines): hand to Codex's built-in `skill-creator` skill and run its draft / test / iterate loop.
- `tune description: <skill path>` (the skill exists but didn't trigger when it should have): hand to `skill-creator` and run its description-optimization loop.
- `new skill via skill-creator: <kebab-name>`: hand creation to `skill-creator`. Do not invent the shape ad hoc.

If your environment ships a SKILL.md validator, run it on every touched skill before declaring done.

## 6. Summarize for the user

Short list, no preamble:

- Edits applied: `<skill path>`. What changed, one line each.
- New skills created: `<skill path>`. One line each (rare).
- Backlog filed to the devex tracker: `<issue title>` (`<tags>`). One line each.
- Dropped: one line per rejected finding + reason from the synthesizer.
