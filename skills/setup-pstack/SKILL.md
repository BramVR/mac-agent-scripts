---
name: setup-pstack
description: "Configure PStack models and reasoning budget per role."
---

# Setup pstack

_Source: [PStack](https://github.com/cursor/plugins/tree/main/pstack/skills/setup-pstack), MIT license._

Write `${CODEX_HOME:-$HOME/.codex}/skills/poteto-mode/references/models.md`, the models file that sets pstack's model per role.

## Steps

### 1. Detect available models

Enumerate the model slugs you can pass to a Codex collaboration agent in this session. That is the dependable source. If Codex also exposes a models API or CLI that lists the user's entitled models, prefer it for completeness. If you cannot detect any, ask the user to paste the slugs they have access to. Never write a real slug you have not confirmed is available. The aliases `inherit-parent` and `auto` are always valid even though they are not detected slugs.

### 2. Load current state

The default role-to-model mapping is the rule shape shown in step 5 below. If `${CODEX_HOME:-$HOME/.codex}/skills/poteto-mode/references/models.md` already exists, read its `# budget` line and role values as the current choices. If the budget line is absent, treat it as `unlimited`. Otherwise start from the defaults.

### 3. Budget, map, and confirm

**(a) Ask for a budget.** Show the current budget and offer four choices:

- `unlimited — keep role defaults`
- `large — xhigh reasoning`
- `medium — high reasoning`
- `small — medium reasoning`

**(b) Apply it.** Start from the skill defaults. On a re-run, retain each role whose model, panel list, or alias (`inherit-parent`, `auto`) differs from the default. `unlimited` leaves those efforts unchanged. The other budgets set every real model entry, including panel entries, to their named effort. Codex passes model and `reasoning_effort` separately. Use the selected model's highest supported effort at or below the budget target when the exact effort is unavailable; if none is supported, mark that entry as needing a choice. Leave aliases unchanged.

**(c) Show the roles and confirm.** Show every role with its model and effort, marking unsupported choices as needing a choice. Ask whether to accept as-is or change specific roles, offering the detected models plus `inherit-parent` and `auto` (both mean: this role runs on the parent chat model, which is how Auto users stay on Auto) as the options. Prefer structured choices over free text. For panel roles (arena runners, architect runners, interrogate reviewers) the value is a list, and one subagent runs per entry, alias entries included, so the list length sets the count. `arena cross-judge pool` is also a list, but Arena selects one value from it whose model family differs from the parent's when possible. `swarm workers` is the default model for every worker unless a race or comparison assigns another model per arm.

### 4. Validate

Every real model and its effort must be supported. `inherit-parent` and `auto` always pass. If a chosen model or effort is unavailable, stop and ask again.

### 5. Write the rule

Write `${CODEX_HOME:-$HOME/.codex}/skills/poteto-mode/references/models.md` with the chosen `# budget` line and one line per role, using the same labels poteto-mode uses. Overwrite the whole file so re-runs stay idempotent. Shape:

```
---
description: pstack per-role model choices (overrides skill defaults)
---

# pstack model configuration

One line per role. Delete a line to fall back to the skill default.

# budget: unlimited (keep role defaults)

`inherit-parent` or `auto` as a value: the role runs on the parent chat model (omit `model`). Alias entries in a panel list still count toward its fan-out.

`<slug>` at `<effort>`: pass the slug as `model` and the effort as `reasoning_effort` on the collaboration agent. `claude-fable-5-1` entries run through `claude -p --model claude-fable-5-1 --effort <effort>`.

- feature, refactoring: `gpt-5.6-sol` at `high`
- bug-fix: `gpt-5.6-sol` at `high`
- perf-issue: `gpt-5.6-sol` at `high`
- hillclimb: `gpt-5.6-sol` at `high`
- judgment and prose: `gpt-6-astra` at `medium`
- hardest tasks: `gpt-6-astra` at `high`
- how explorer: `gpt-5.6-luna` at `high`
- how explainer: `gpt-5.6-sol` at `high`
- why investigators: `gpt-5.6-luna` at `high`
- why synthesizer: `gpt-5.6-sol` at `high`
- reflect tooling: `gpt-5.6-sol` at `high`
- reflect judgment, divergent, synthesizer: `gpt-6-astra` at `medium`
- arena runners: `gpt-5.6-sol` at `high`, `gpt-5.6-terra` at `high`, `gpt-5.6-luna` at `high`
- arena cross-judge pool: `gpt-6-astra` at `medium`, `gpt-5.6-sol` at `high`
- swarm workers: `gpt-5.6-luna` at `high`
- architect runners: `gpt-5.6-sol` at `high`, `gpt-6-astra` at `low`, `claude-fable-5-1` at `high`
- interrogate reviewers: `gpt-6-astra` at `high`, `gpt-5.6-sol` at `high`, `claude-fable-5-1` at `xhigh`
- Comment Sicko: `gpt-5.6-luna` at `high`
```

### 6. Confirm

Tell the user the rule was written and that it applies to new sessions. Re-running this skill updates it.

### 7. Offer a verification skill (optional)

Check whether the project has a way to drive the real app for proof (a `verify-*` skill, or an existing harness). If not, offer once: "want a project-local verification skill, so agents can drive the app the way a user does and prove changes work? I can generate one with $create-verification-skill." On yes, invoke `$create-verification-skill` (resolves wherever pstack is installed: workspace, user, or plugin). On no, move on without pushing.
