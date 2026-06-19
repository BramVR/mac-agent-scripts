---
summary: "Start one Bram maintainer loop for a project."
read_when:
  - Starting a delegated maintainer loop for one repository.
---

# Bram Maintainer Project Loop

Use $bram-maintainer-loop for <repo-or-owner/repo>.

Goal: triage the current queue, pick autonomous issues/PRs, and prepare decision-ready PRs. Use $github-project-triage as the worker skill for queue mapping and issue/PR execution.

Authorized: triage, create/rename worker threads, implement autonomous items, create focused branches, commit, push branches, create/update PRs, rerun/watch CI, and make CI repair commits until green.

Not authorized: merge, close, release, destructive cleanup, unrelated workflow/secret changes, or broad work outside this repository.

Rules: one issue per fresh worker; reuse only the worker already assigned to the exact same issue. Workers must not subdelegate. Use TDD for behavior changes unless trivial/docs-only. Run tests, live proof when applicable, autoreview, CI, and public-artifact audit before asking Bram.

Architecture: do not run improve-codebase-architecture automatically. If repeated issue work exposes hard-to-test modules, shallow modules, unclear seams, or cross-cutting refactor pressure, report it as Ready next for a separate architecture pass.

Report: Active, Needs Bram, Ready next. Use full GitHub URLs. Ask only for exact land/delete/access/waiver decisions after autonomous work is exhausted.
