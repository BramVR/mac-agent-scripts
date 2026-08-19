---
name: tdd
description: "Test-driven development. Use when the user wants to build features or fix bugs test-first, mentions red-green-refactor, or wants integration tests."
---

# Test-Driven Development

_Source: [mattpocock/skills](https://github.com/mattpocock/skills), synced from `main` at `885e2ca4`; adapted for Bram's autonomous maintainer loop._

TDD is the red -> green loop. This skill is the reference that makes that loop produce tests worth keeping: what a good test is, where tests go, the anti-patterns, and the rules of the loop. Every section applies on every cycle. Consult them before and during the loop, not after.

When exploring the codebase, read `CONTEXT.md` if it exists so test names and interface vocabulary match the project's domain language, and respect ADRs in the area you're touching.

## What a good test is

Tests verify behavior through public interfaces, not implementation details. Code can change entirely; tests shouldn't. A good test reads like a specification. "User can checkout with valid cart" says exactly what capability exists, and it survives refactors because it doesn't care about internal structure.

See [tests.md](tests.md) for examples and [mocking.md](mocking.md) for mocking guidelines.

## Seams: where tests go

A **seam** is the public boundary you test at: the interface where you observe behavior without reaching inside. Tests live at seams, never against internals.

**Test only at pre-agreed seams.** Before writing any test, write down the seams under test and confirm them with the user. No test is written at an unconfirmed seam. You can't test everything, so agreeing the seams up front is how testing effort lands on the critical paths and complex logic instead of every edge case.

Ask: "What's the public interface, and which seams should we test?"

When the shape of that interface is itself in question, call the Skill tool with "codebase-design" for the vocabulary. It is the shared source of the module, interface, depth, seam, adapter, leverage, and locality terms. Consult it as a reference, not a session to run.

In `bram-maintainer-loop-v2`, an item classified as autonomous with implementation authority already has approval for its agreed tracer-bullet seam. Ask Bram only when test scope, a product or API contract, security, or live-proof access still needs a decision.

## Anti-patterns

- **Implementation-coupled**: mocks internal collaborators, tests private methods, or verifies through a side channel such as querying the database instead of using the interface. The tell is a test that breaks after a refactor even though behavior did not change.
- **Tautological**: the assertion recomputes the expected value the same way the code does, so it passes by construction and cannot disagree with the implementation. Expected values must come from an independent source of truth such as a known-good literal, worked example, or specification.
- **Horizontal slicing**: writing all tests first, then all implementation. Bulk tests verify imagined behavior and commit to test structure before the implementation teaches you what matters. Work in vertical slices instead: one test -> one implementation -> repeat. Each test is a tracer bullet that responds to what the last cycle taught you.

## Rules of the loop

- **Red before green.** Write the failing test first, then only enough code to pass it. Don't anticipate future tests or add speculative features.
- **One slice at a time.** One seam, one test, one minimal implementation per cycle.
- **Refactoring is not part of the loop.** It belongs to the review stage, not the red -> green implementation cycle. Never refactor while red.
