---
description: pstack per-role model choices (overrides skill defaults)
---

# pstack model configuration

One line per role. Delete a line to fall back to the skill default.

# budget: unlimited (keep role defaults)

`inherit-parent` or `auto` as a value: the role runs on the parent chat model (omit `model`). Alias entries in a panel list still count toward its fan-out.

`<slug>` at `<effort>`: pass the slug as `model` and the effort as `reasoning_effort` on the collaboration agent. Claude entries run through `claude -p --model <slug> --effort <effort>`; `claude-opus-5-5` requires Claude Code 2.1.280 or newer.

- feature, refactoring: `gpt-6-sol` at `high`
- bug-fix: `gpt-6-sol` at `high`
- perf-issue: `gpt-6-sol` at `high`
- hillclimb: `gpt-6-sol` at `high`
- judgment and prose: `gpt-6-astra` at `medium`
- hardest tasks: `gpt-6-astra` at `high`
- how explorer: `gpt-6-luna` at `high`
- how explainer: `gpt-6-sol` at `high`
- why investigators: `gpt-6-luna` at `high`
- why synthesizer: `gpt-6-sol` at `high`
- reflect tooling: `gpt-6-sol` at `high`
- reflect judgment, divergent, synthesizer: `gpt-6-astra` at `medium`
- arena runners: `gpt-6-astra` at `medium`, `gpt-6-sol` at `high`, `gpt-5.6-sol` at `high`, `claude-opus-5-5` at `high`, `claude-fable-5-1` at `high`
- arena cross-judge pool: `gpt-6-astra` at `medium`, `gpt-6-sol` at `high`, `claude-opus-5-5` at `high`
- swarm workers: `gpt-6-luna` at `high`
- architect runners: `gpt-6-sol` at `high`, `claude-opus-5-5` at `high`, `claude-fable-5-1` at `high`
- interrogate reviewers: `gpt-6-astra` at `high`, `gpt-6-sol` at `high`, `claude-opus-5-5` at `xhigh`
- Comment Sicko: `gpt-6-luna` at `high`
