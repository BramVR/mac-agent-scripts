---
name: craft-prompt
description: "Turn rough notes, source text, or an existing prompt into a production-ready GPT-5.6 prompt through a one-question-at-a-time interview. Use when the user asks to craft, improve, structure, or debug a prompt and material requirements may be incomplete."
---

# Craft Prompt

Turn supplied knowledge into one lean, outcome-first prompt. Interview only where missing decisions would materially change the result.

Before interviewing or drafting, retrieve the current official [GPT-5.6 prompting guide](https://developers.openai.com/api/docs/guides/prompt-guidance-gpt-5p6). Prefer OpenAI developer-docs search/fetch tools; otherwise use available web retrieval restricted to `developers.openai.com`.

Use the retrieved guide as the source of truth. If online retrieval is unavailable or fails, read [references/gpt-5p6-guidance.md](references/gpt-5p6-guidance.md) instead and briefly disclose that bundled fallback guidance was used. Do not let retrieval failure block prompt construction.

## Build the brief

1. Read all supplied notes, text, files, and existing prompt fragments.
2. Extract internally:
   - explicit user values and facts;
   - desired outcome;
   - success criteria;
   - available inputs or evidence;
   - constraints and permission boundaries;
   - tools or external capabilities;
   - output requirements;
   - stopping, fallback, and validation rules;
   - contradictions, assumptions, and material gaps.
3. Do not ask for information already present or safely inferable.
4. Inspect supplied materials for discoverable facts instead of asking the user. Put decisions to the user.
5. Preserve explicit values. Never replace them with generic defaults.

For an existing prompt, establish its working baseline before editing. Ask for the observed failure, desired behavior, and representative trace or evaluation when missing. Prefer the smallest change that addresses a measured problem; do not rewrite the full prompt stack merely to modernize its style.

If the user supplies no notes, ask first for an unfiltered dump. Recommend pasting everything they know, including uncertainty, examples, constraints, and the desired result.

## Interview

Ask exactly one question per turn. Choose the unresolved decision with the greatest downstream effect. Follow dependencies; do not march through a static checklist.

Use this compact shape:

```text
Question — <decision>
<one focused question>

Recommended: <specific answer> — <brief reason grounded in the notes>.

Reply “recommended”, choose another option, answer freely, or say “discuss”.
```

Add at most two concise alternatives only when they clarify a real tradeoff. Never recommend a vague placeholder such as “it depends.” Make the best contextual judgment and state its tradeoff.

Accept any of these interaction modes:

- `recommended`: record the recommended answer and continue.
- Another option or free text: record it faithfully; surface a contradiction only if material.
- `discuss` or a question: answer directly, explain the tradeoff, then restate the still-open decision with an updated recommendation. Do not treat discussion as consent.
- `just draft`: stop interviewing, make conservative assumptions, list only material assumptions briefly, then draft.
- Correction of an earlier answer: update the brief and revisit dependent decisions only when necessary.

Ask only about applicable gaps. Typical decision order:

1. User-visible outcome and intended use.
2. Audience, operating context, and target model or surface when it changes behavior.
3. Completion bar and observable success criteria.
4. Inputs, evidence, and treatment of missing or conflicting information.
5. Safety, business, scope, permission, and side-effect boundaries.
6. Tool routing and autonomy for agentic prompts.
7. Required output content, structure, language, length, and tone.
8. Personality and collaboration behavior for user-facing assistants.
9. Retry, fallback, abstention, clarification, and stopping rules.
10. Validation or evaluation requirements.

Skip resolved or irrelevant areas. Avoid asking for cosmetic preferences before functional decisions.

## Draft

When no material gap remains, draft immediately; no ceremonial confirmation round.

Construct the shortest prompt that reliably captures the brief:

- Lead with the outcome and completion bar.
- Describe the destination; leave routine reasoning and process choices to the model.
- Include only applicable sections from: `Role`, `Personality`, `Goal`, `Success criteria`, `Inputs`, `Constraints`, `Tools`, `Output`, `Stop rules`.
- Keep personality and collaboration instructions short and behavioral.
- Use decision rules for judgment calls. Reserve `always`, `never`, `must`, and `only` for true invariants.
- State permission boundaries once. Distinguish read-only work, in-scope changes, and actions requiring confirmation when relevant.
- Define tool prerequisites, routing, fallback behavior, and error handling only when tools matter.
- Define evidence and citation behavior for grounded work. Never turn missing evidence into an unsupported factual claim.
- Preserve requested facts, values, artifact type, genre, and structure. Do not invent claims to improve the draft.
- Add explicit validation and stop conditions for multi-step or high-stakes work.
- Remove repeated rules, inert examples, irrelevant tools, generic reassurance, and contradictions.
- Keep stable reusable instructions before variable runtime input. Use meaningful placeholders only for missing runtime values.
- Keep API controls such as reasoning effort or `text.verbosity` outside the prompt when the runtime exposes them directly.

## Deliver

Return:

1. `Assumptions used` only when the user requested an immediate draft with material gaps.
2. `Prompt` as one copyable artifact.
3. `Runtime settings` only when an API-level setting materially affects the intended behavior.

Do not append a long explanation, prompt-engineering lecture, or alternate prompt unless asked.

Before sending, verify:

- every explicit user decision is preserved;
- outcome, success criteria, constraints, output, and stop rules do not conflict;
- every section changes behavior;
- factual and creative content remain distinguishable;
- the prompt says what completion means;
- the result is ready to paste or has clearly labeled runtime placeholders.
