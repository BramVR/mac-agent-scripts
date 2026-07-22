# GPT-5.6 prompt guidance

Source: [OpenAI, Prompting guidance for GPT-5.6 Sol](https://developers.openai.com/api/docs/guides/prompt-guidance-gpt-5p6)  
Companion: [OpenAI, Using GPT-5.6](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-5.6)  
Verified: 2026-07-14

Use this as a construction and review checklist. It is a concise interpretation of the official guide, not a replacement for model-specific evaluation.

The official guide does not prescribe an interview workflow. The one-question loop in this skill is a derived application of its guidance to preserve explicit values, request the smallest missing field, and stop once the task is answerable.

## Core contract

Define four things clearly, then leave room for efficient execution:

- outcome;
- important constraints;
- available evidence;
- completion bar.

Prefer destination and success criteria over a prescribed reasoning path. Preserve explicit user values. Use decision criteria for implicit choices rather than universal defaults or keyword maps.

## Keep and trim

Keep:

- user-visible outcome;
- success criteria and stopping conditions;
- safety, business, evidence, permission, and side-effect constraints;
- contextual tool-routing rules;
- required output and validation.

Trim:

- duplicate rules;
- style or process instructions that do not alter behavior;
- inert examples;
- scaffolding for behavior the model already handles reliably;
- unrelated tools and descriptions.

Resolve contradictions before adding detail. Use absolute language only for true invariants.

## Collaboration and output

Keep personality and collaboration style separate and short:

- personality: tone, warmth, directness, formality, empathy, polish;
- collaboration: questions, assumptions, initiative, tradeoffs, checks, uncertainty.

Specify concrete writing behavior instead of broad labels. For short outputs, identify required information to preserve and lower-value detail to omit. Use runtime `text.verbosity` for default detail when available; keep task-specific format and content in the prompt.

For editing or rewriting, explicitly preserve the requested artifact, factual claims, length, structure, and genre before improving clarity or flow.

## Autonomy and tools

Define authorization by request type and risk. Permit safe, in-scope work without repeated approval. Require confirmation for external writes, destructive or costly actions, and material scope expansion.

Expose only relevant tools. Describe:

- what each tool does;
- when to use it;
- important return fields;
- error and fallback behavior.

Require prerequisite discovery or validation when correctness depends on it. Parallelize independent reads; keep dependent decisions sequential. Try a small number of meaningful fallbacks for empty or suspicious results.

## Evidence and state

For grounded work, define:

- which claims require support;
- sufficient evidence;
- citation placement;
- behavior when evidence is absent or conflicting;
- retrieval budget and stop condition.

Label inference. Do not invent facts for creative polish.

For long work, request a brief preamble and sparse milestone updates, not routine narration. Keep reusable prompt prefixes stable when caching matters. Persist prior reasoning only while the objective and assumptions remain stable.

## Validation

Name the checks that establish success. If checks cannot run, require a reason and the next-best check. Before increasing reasoning effort, first look for a missing success criterion, dependency rule, tool rule, or verification loop.

For complex prompts, select only useful sections from:

```text
Role
Personality
Goal
Success criteria
Constraints
Tools
Output
Stop rules
```

Keep each section short. Add detail only when it changes behavior. Test prompt changes on representative tasks and make surgical revisions from observed failures.
