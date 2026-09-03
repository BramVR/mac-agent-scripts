---
name: swarm
description: "Fan out N parallel workers, drain them, and return one report. Use for $swarm, 'swarm this', or parallel coverage, races, gauntlets, and exploration."
---

# Swarm

Fan out N parallel Codex subagents. They may cover separate slices, race the same brief, or mix both. The parent waits, aggregates, and returns one report.

## Start

Open a plan with one entry per phase before launching anything.

1. Frame
2. Fan out
3. Aggregate
4. Report

## Phase A: Frame

1. State the done predicate and the artifact or report the swarm must return.
2. Choose the shape. Partition into slices, race N workers on identical briefs, or mix both. For a race or mixed shape, declare `first pass`, `rank all`, or `best-of` before spawning.
3. Set N from the user or derive it from the shape. N is total workers, not the Codex concurrency limit. When N exceeds the available limit, run workers in waves.
4. Use `gpt-5.6-luna` at `high` reasoning for every worker. Never use fast mode or substitute another model or reasoning level. For a model race, use the models named by the caller. For any other race, name each arm up front and keep Luna.
5. Give each worker its own writable output when it writes. Use an authorized Codex worktree, branch, or `/tmp/swarm-<slug>/worker-<n>/`.

## Phase B: Fan out

Spawn all N workers as Codex collaboration agents in one concurrent batch when capacity allows and otherwise in waves, each with `model: "gpt-5.6-luna"`, `reasoning_effort: "high"`, and `fork_turns: "none"`, unless Phase A declared a caller-specified model race.

When a worker must start from a non-default pushed branch, use an authorized Codex worktree chat based on that branch.

Every brief stands alone. Include the goal, scope, exact slice or race arm, how to verify, and what to report. Reports use `PASS`, `ISSUES`, or `BLOCKED` with evidence.

If a worker drops out, proceed with N-1 and note it.

## Phase C: Aggregate

Read the collaboration-agent results. For coverage, every required slice needs a result. For a race, apply the selection rule declared up front. Use first pass, rank all, or best-of. Do not paste raw worker dumps.

Keep a compact result table, one-line evidenced issues, and explicit gaps or dropouts.

## Phase D: Report

Return one consolidated in-chat report with the table, issue one-liners, gaps or dropouts, and the race rule when used.
