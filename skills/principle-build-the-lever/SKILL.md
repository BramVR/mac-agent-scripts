---
name: principle-build-the-lever
description: "Build a rerunnable tool for non-trivial repetitive or auditable work."
---

# Build the lever

_Source: [PStack](https://github.com/cursor/plugins/tree/main/pstack/skills/principle-build-the-lever), MIT license. Adapted for Codex tooling and delegation rules._

When work is non-trivial, build the smallest tool that performs or proves it instead of relying on hand edits.

## Decide

Skip the lever only when the work is a couple of obvious edits that can be checked at a glance. A one-off still deserves a lever when auditability matters.

Useful levers include:

- a codemod or script for coordinated edits;
- a generator for repeated files;
- a query or extractor for analysis;
- a rerunnable check for verification;
- a skill containing one shared recipe and safety boundary when the user explicitly requests delegated work.

Prefer one deterministic pass over agents repeating a mechanical recipe by hand.

## Build

1. Do one representative unit manually to learn the recipe.
2. Build the smallest script, generator, query, or check that captures it.
3. Make reruns safe. Prefer idempotent behavior and explicit inputs and outputs.
4. Run it against the representative unit and compare its result with the manual version.
5. Run it over the full scope.

Keep the lever in the repository when the work or proof will recur. A task-local script is enough when it only supports the current investigation.

## Prove

The lever is part of the result. Report its path, invocation, and observed result. If no rerunnable artifact exists, do not claim this skill was applied.

Use `$principle-prove-it-works` to verify the real output after the lever runs.
