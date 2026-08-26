---
name: maintain-verification-skill
description: "Audit a project-local verification skill against current source and live behavior. Use when a verify-<app> feature map or its launch, doctor, drive, evidence, or cleanup instructions may have drifted."
---

# Maintain a verification skill

Keep a project-local verification skill honest as the app changes. Cover every mapped feature from source and exercise every feature live. Audit features, not every sentence or bullet.

## Outcomes

Report exactly one outcome:

- `clean`: every feature received source and live coverage; nothing needs changing.
- `changed`: verified corrections were made inside the verification skill directory.
- `blocked`: coverage could not finish or a proven correction could not be made safely. Name the blocker and uncovered features.

Do not create a branch, commit, push, or PR unless the user asked for that action. A clean or blocked run does not need repository history changes.

## Scope

Only edit the target verification skill directory: its `SKILL.md`, `features/`, `agents/`, and helpers it owns. Do not edit product code during this audit.

Treat mismatches by cause:

- The app intentionally changed and the verification instructions are stale. Fix the skill or feature map.
- The app works but the owned helper cannot drive it. Fix the helper and document its invocation.
- The documented behavior should still work but the app is broken. Report a product regression. Do not rewrite the map to make the regression look intentional.

## Locate the target

Find the project-local skill with launch and drive instructions plus a feature map, normally `.agents/skills/verify-*/`. If exactly one exists, use it. If several exist and the request does not identify one, ask which target to audit. If none exists, stop and recommend `$create-verification-skill`.

Read the target skill completely before driving anything. Its ownership, isolation, doctor, evidence, and cleanup rules govern the run.

## Check the feature index

Read `features/README.md` and list its sibling feature files. Fix missing, extra, duplicate, or dead index entries. Do not generate a redundant inventory.

## Review every feature from source

For each feature file:

1. Explain how the user-facing behavior currently works from source.
2. Cite the source entry points that establish it.
3. Compare every documented user entry point, prerequisite, stable handle, and observable result with current code.
4. Record likely drift or `none`.
5. Produce one concise live recipe that covers the feature.

Read the features directly by default. When the user explicitly asks for parallel agent work and delegation is available, one read-only agent may inspect each feature concurrently. Delegated readers never drive the app or edit files. Verify their claims against cited source before changing anything.

Sweep recent user-facing changes for features absent from the map. Require a concrete source path before adding one. Reconcile overlapping recipes into as few app states as practical.

## Drive every feature

Live coverage is required even when source review looks clean. Follow the target skill's launch model:

- Use one owned long-lived instance and drive it serially for servers and UIs.
- Use a fresh isolated session per drive for short-lived CLIs and TUIs.

Exercise every feature at least once. Do not claim one entry point covers another. Keep these invariants throughout the pass:

- Run doctor before the first drive, for every fresh session, and after any surprising or failed drive. If doctor cannot detect a wedged UI state, restore a known state or relaunch.
- Check that captured evidence still exists after every cleanup.
- Remove task-owned residue after each drive once it is no longer useful. On a shared instance, remove only task-owned residue, never the instance.
- Do not perform production sends, publications, purchases, destructive mutations, or other externally consequential actions without the user's specific authorization. Record the path as unreachable when safe proof needs missing authority or isolation.

If doctor fails because its instructions drifted, fix the verification skill, restart only what the correction invalidated, and retry once. A second failure makes the run blocked.

Mark a feature `verified-unreachable` only when you record the attempted route and concrete missing prerequisite, such as authentication, entitlement, hardware, operating system, or external state. If the map omitted that prerequisite, correct the map.

Re-drive every helper correction before accepting it. After the final drive and any reproof, run the target skill's teardown. Evidence must remain; task-owned processes and scratch state must not.

## Finish

Re-read every changed file and inspect the final diff. Keep uncommitted run notes in a scratch location. Record features covered, unreachable prerequisites, confirmed drift, product regressions, and the outcome.

For `changed`, report the local corrections and proof. Commit or open one PR only when the user requested it. For `clean` or `blocked`, make no publication changes and report coverage honestly.
