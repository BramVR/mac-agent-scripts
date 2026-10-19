# pstack model configuration (T3, Codex host).
# Preserves the local Codex role choices. Mixed panels are intentional.
# budget: unlimited (keep role defaults)
feature, refactoring: codex/gpt-6.1-sol reasoningEffort=high
bug-fix: codex/gpt-6.1-sol reasoningEffort=high
perf-issue: codex/gpt-6.1-sol reasoningEffort=high
hillclimb: codex/gpt-6.1-sol reasoningEffort=high
judgment and prose: codex/gpt-6-sol reasoningEffort=high
hardest tasks: codex/gpt-6.1-sol reasoningEffort=high
how explorer: codex/gpt-6.1-sol reasoningEffort=low
how explainer: codex/gpt-6.1-sol reasoningEffort=high
why investigators: codex/gpt-6.1-sol reasoningEffort=low
why synthesizer: codex/gpt-6.1-sol reasoningEffort=high
reflect tooling: codex/gpt-6.1-sol reasoningEffort=high
reflect judgment, divergent, synthesizer: codex/gpt-6.1-sol reasoningEffort=high
arena runners: codex/gpt-6.1-sol reasoningEffort=high, claudeAgent/claude-opus-5-5 effort=high, claudeAgent/claude-fable-5-1 effort=high
arena cross-judge pool: codex/gpt-6.1-sol reasoningEffort=high, claudeAgent/claude-opus-5-5 effort=high
swarm workers: codex/gpt-6.1-sol reasoningEffort=low
architect runners: codex/gpt-6.1-sol reasoningEffort=xhigh, claudeAgent/claude-opus-5-5 effort=high, claudeAgent/claude-fable-5-1 effort=high
interrogate reviewers: codex/gpt-6.1-sol reasoningEffort=xhigh, claudeAgent/claude-opus-5-5 effort=xhigh
session hook: on
