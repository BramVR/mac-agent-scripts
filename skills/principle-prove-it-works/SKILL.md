---
name: principle-prove-it-works
description: "Prove completed work through the real artifact and direct observable behavior."
---

# Prove it works

_Source: [PStack](https://github.com/cursor/plugins/tree/main/pstack/skills/principle-prove-it-works), MIT license. Adapted for Codex verification workflows._

Before declaring a task complete, check the real result directly. Compilation, timestamps, cached output, and agent summaries are supporting evidence, not proof of behavior.

## Choose the proof

Ask: what direct observation would fail if this work were wrong?

- Code: build it, run the real feature path, and check the input-to-output chain.
- Integration: exercise the full communication path when safe and authorized.
- Data or configuration: read the actual stored value, not a derived indicator.
- Process: inspect liveness and identity directly.
- Delegated work: inspect the diff, files, and runtime result; do not rely on the delegate's report.

If the real path is unavailable, name the missing prerequisite and the strongest lower-level proof achieved. Do not silently promote a proxy into end-to-end proof.

## Run the proof

1. Record the starting state when residue or mutation matters.
2. Exercise the actual artifact with representative input.
3. Assert the expected output and the important failure case.
4. Check side effects, exit status, and cleanup where relevant.
5. Preserve concise evidence that another person can inspect or rerun.

When a check fails, validate the observation method before blaming the system.

## Make it rerunnable

Prefer a deterministic script over a one-time visual check when the comparison is subtle or repeated. Keep the script when future reviewers will need the same proof; otherwise a visible task-local artifact is enough.

Report the command, artifact path, observed result, and any boundary that remained unverified. Use `$principle-build-the-lever` when the proof itself needs a reusable tool.
