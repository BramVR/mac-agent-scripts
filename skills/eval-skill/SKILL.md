---
name: eval-skill
description: "Run a blinded behavioral comparison of a Codex skill variant against a baseline. Use when deciding whether a new or changed skill improves agent behavior before promotion."
---

# Evaluate a skill

Test how a skill changes agent behavior. Keep candidate runs blind, isolate every run, grade real artifacts, and separate skill effects from model effects.

## Define the comparison

Resolve the target skill and comparison arms before running anything.

- Prefer an explicit pair of skill paths or revisions.
- For a tracked modified skill, compare the working version with its version at the requested base revision, or `HEAD` when no base was named.
- For a new skill, use a no-skill baseline only when that answers the user's question. Otherwise ask what should serve as the baseline.
- Never edit the target skill during a run. A revision creates a new experiment.

State the behavior under test and write a held-back rubric with three to six observable criteria. Criteria should distinguish the variants through output quality, decisions, code shape, verification, or safety. Do not grade prose that merely repeats the skill.

Choose one realistic user request. Use the user's supplied task when possible. Otherwise derive a task from the skill's description and resources. Ask only when several plausible tasks would exercise different behavior.

## Blind the candidates

Candidate agents must not know they are part of a comparison.

- Do not introduce `eval`, `test`, `judge`, `experiment`, `rubric`, `score`, `compare`, `benchmark`, `candidate`, `variant`, `baseline`, `arm`, or `arena` into evaluator-owned directory names, filenames, instructions, or prompts candidates can see. Existing organic project files may keep their natural names.
- Give each run a natural project-shaped directory name.
- Use the same organic user request for every run. State the goal, not what is being measured.
- Do not mention other runs, models, the held-back criteria, or expected behavior.
- Do not ask agents to name skills, principles, files read, or reasoning steps.

It is normal for an agent to see the skill it is expected to use. Provide the arm's skill instructions through the environment's normal skill-injection mechanism. If that is unavailable, place the skill under `.agents/skills/<skill-name>/` in the isolated project and instruct the agent to read it before executing the organic request. Do not expose this evaluator's path or instructions.

## Build isolated environments

Create one task-owned scratch directory per run. Copy only the minimum project skeleton, fixtures, and context the organic task needs. Install one comparison arm in each directory. Give both arms equivalent tools, permissions, dependencies, and starting state.

Do not use a live user checkout, shared application state, production credentials, or real customer data. Candidate tasks that would send, publish, purchase, delete, or mutate external state need a safe fake boundary or the user's specific authorization. Preserve the candidate outputs and proof; remove task-owned runtime residue after each run.

Use natural labels for directories and artifacts. Keep the private arm-to-label mapping outside anything candidates or the judge can read.

## Run paired attempts

Use the same model and reasoning effort for both arms in a pair. Launch paired agents concurrently when isolation and available slots allow it. Use `fork_turns: "none"` or the narrowest context fork so candidates do not inherit evaluator instructions.

One pair is a smoke comparison. Use two or more pairs when nondeterminism matters or the decision is expensive. To check generality across models, run every selected model against every arm. Never assign different models exclusively to different arms.

Each candidate receives only:

1. Its isolated project path and the requirement to work only there.
2. The normal skill injection or neutral instruction to read its installed project skill.
3. The organic user request.

Wait for every run. Record failures and dropouts. Do not silently replace them with extra attempts.

## Inspect behavior

Read every output and artifact end to end. Inspect diffs, files, commands, runtime proof, and cleanup state. Re-run safe deterministic checks when needed.

When task-scoped Codex transcripts or tool records are available, inspect which instructions and files the agent actually read. Do not scan unrelated task histories. Do not trust candidate claims about what they followed. If the environment does not expose that evidence, mark instruction reading `unobserved` and grade the artifact instead.

## Judge blind

Give one independent judge all outputs in one pass, using sanitized labels and one shared rubric. Hide arm identity, model identity, run order, and the private mapping. A different model family is useful when available, but consistent calibration matters more than novelty.

The judge returns, for each label:

- criterion-level evidence and rating;
- failures or missing proof;
- overall ranking and confidence;
- rubric ambiguity that prevented a clean decision.

The coordinator then reads every artifact and compares its own assessment with the judge. Treat disagreement as a sign of ambiguous criteria, weak evidence, or judge bias. Do not average away a disputed result. At most one rubric correction and clean rerun belongs in the same evaluation; further changes need a new run.

## Report

Return:

- skill and baseline under comparison;
- organic request and held-back rubric;
- run matrix with sanitized labels, models, and completion status;
- evidence and criterion results for every run;
- judge verdict and coordinator assessment;
- limitations, including unobserved instruction reads;
- recommendation: `promote`, `do not promote`, or `inconclusive`.

Keep the private label mapping and task-owned artifacts in a named scratch location until the user accepts the result. Do not change, commit, push, or publish the skill unless the user asks.
