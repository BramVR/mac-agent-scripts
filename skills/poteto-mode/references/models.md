---
description: pstack per-role model choices (overrides skill defaults)
---

# pstack model configuration

One line per role. Delete a line to fall back to the skill default.

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
- architect runners: `gpt-5.6-sol` at `high`, `gpt-5.6-terra` at `high`, `gpt-5.6-luna` at `high`
- interrogate reviewers: `gpt-6-astra` at `high`, `gpt-5.6-sol` at `high`, `claude-fable-5-1` at `xhigh`
- Comment Sicko: `gpt-5.6-luna` at `high`
