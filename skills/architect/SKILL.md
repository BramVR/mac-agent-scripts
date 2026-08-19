---
name: architect
description: "Sketch types, signatures, and module structure before code. Use for $architect, architecture design, or non-trivial work where coding first risks the wrong shape."
---

# Architect

_Source: [PStack](https://github.com/cursor/plugins/tree/main/pstack/skills/architect), MIT license. Adapted only where its original orchestration assumes Cursor-specific skills or model configuration._

Design before implementing. Sketch types, function signatures, class shapes, and module boundaries with `not implemented` bodies and pseudocode. Synthesize across multiple perspectives, then fill in code against the chosen sketch. If implementation proves the sketch wrong, throw it out and redesign.

## Start

Open a task plan with one entry per phase before starting. Autonomous mode without checkpoints needs the list to show phase position and keep phases from silently disappearing.

1. Ground
2. Sketch
3. Agree
4. Implement
5. Scrap

## Phase A: Ground the problem

Build a real mental model of every system the new code touches. If the `how` skill is available, run it over the relevant subsystems; otherwise trace the callers, data flow, state transitions, and runtime behavior directly. Use critique mode if existing structure is the constraint or the design must push back on it.

Naming a file isn't grounding. Produce a traced model. If the design redefines ownership or layering, use the `why` skill when available; otherwise inspect documentation, history, issues, and source rationale so the existing shape becomes a constraint, not a guess.

Skip Phase A only when the work is genuinely greenfield with no surrounding system to integrate.

## Phase B: Sketch

Produce at least two structurally distinct design candidates before synthesis, even when the first looks sufficient. Whole-shape alternatives, not point fixes inside one shape.

If the `arena` skill is available, run it with the design-sketch task, the Phase A grounding artifacts, and `references/runner-prompt.md`. If it is unavailable, produce the alternatives directly. When the user explicitly requests parallel agent work, independent Codex agents may each produce one candidate using that runner prompt.

Each candidate produces a design package shaped per `references/rationale-template.md`: the caller's usage written first, then the type sketch, function signatures, module map, and prose rationale derived from it.

Screen every candidate against [`references/design-red-flags.md`](references/design-red-flags.md) before synthesis. Reject or revise shallow modules, information leakage, temporal decomposition, and pass-through methods.

Compare viable candidates on interface depth. Prefer the design that hides more complexity behind a smaller, simpler public surface. A rich interface can keep call chains short by concentrating capability instead of scattering it across layers.

Synthesize one design package and populate the rationale's "Synthesis decision" section.

## Phase C: Agree (opt-in)

For a design-only or review-only request, return the synthesized design package and stop. Enter Phase D only when the original request includes implementation, building, or fixing.

For implementation requests, proceed directly with the synthesized design by default. No human checkpoint.

Opt in to a checkpoint when the invoker explicitly asks: "$architect with checkpoint", "stop and show me before implementing", or similar. Then surface the synthesized design and pause for sign-off.

The synthesis can ship as its own commit either way. Subsequent commits fill in bodies against a stable contract. Planned and scoped breakage during fill-in is fine. For adversarial pressure on the design before implementing, use the `interrogate` skill when available or an explicitly requested independent review.

If the human pushes back on the shape, treat that as Phase A evidence. Re-ground and re-run Phase B before writing more code.

## Phase D: Implement against the sketch

Replace `not implemented` bodies with code, pseudocode with logic. The synthesized sketch is the contract.

Deviations from the sketch are signal worth surfacing, not friction to absorb silently. If a function needs a parameter the sketch didn't anticipate, ask whether the sketch was wrong, the requirement was missed, or the implementation is overreaching. Surface it; don't bolt it on.

## Phase E: Scrap when the architecture is wrong

If implementation keeps producing friction the sketch can't absorb, throw the sketch out. Don't bolt fixes onto a wrong design.

The signal is a *pattern*, not single instances. Tells:

- The same shape of workaround appearing repeatedly across unrelated code.
- Multiple unrelated edge cases that all need special-case branches.
- Types that need escape hatches (`any`, casts, optional fields always set in practice) to compile.
- The "we need a lock" reflex when the sketch said the state wasn't shared.
- Callers having to know the abstraction's internal rules to use it.
- Two or more independent Phase D deviations of the same shape across the implementation.

Use judgment. A few edge cases don't condemn an architecture. Some problems are legitimately complex; complexity in the data is not complexity in the design. The rewrite signal is repeated friction of the same shape, not single hard cases.

When you scrap:

1. Re-ground over what's been built. The implementation lessons enter the new design as inputs, not vibes.
2. Redesign as if the new constraints had been day-one assumptions.
3. Subtract before adding. The new sketch should be smaller than the old one before it grows.
4. Return to Phase B.

## Outputs

Write the caller's usage first and derive the type sketch from it. Use one file with new types and signatures for small changes; use a module map plus type definitions for larger work. Ship the rationale alongside, shaped per `references/rationale-template.md`, including the usage sketch and synthesis decision.
