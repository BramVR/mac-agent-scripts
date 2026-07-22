---
summary: "Interview rough notes into a production-ready GPT-5.6 prompt."
argument-hint: "[notes, source text, or existing prompt]"
read_when:
  - Crafting or improving a prompt from incomplete source material.
---

# /prompts:craft-prompt

Turn notes, source text, or an existing prompt into a production-ready GPT-5.6 prompt. The skill asks one material question at a time, recommends a concrete answer, and accepts `recommended`, another answer, free discussion, or questions.

Examples:

```text
/prompts:craft-prompt Build a read-only workflow demo prompt for this repository.
/prompts:craft-prompt Improve this existing prompt: ...
```

The compatibility prompt lives at `~/.codex/prompts/craft-prompt.md` and invokes the complete `$craft-prompt` skill. The skill reads current official OpenAI guidance first and falls back to its bundled local reference when online retrieval fails. Custom prompts are deprecated; prefer `$craft-prompt` when a slash alias is unnecessary.
