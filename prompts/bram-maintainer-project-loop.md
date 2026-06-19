---
summary: "Start one Bram maintainer loop for a project."
read_when:
  - Starting a delegated maintainer loop for one repository.
---

# Bram Maintainer Project Loop

Use $bram-maintainer-loop for <repo-or-owner/repo>.

Objective: run one project maintainer loop until autonomous queue work is exhausted or a Bram decision is required.

Scope: only <repo-or-owner/repo>. Use the skill's repository resolution, worker, proof, and reporting rules.

Permissions granted:
- triage and monitor
- create/rename worker threads
- implement autonomous issues/PRs
- create focused branches
- commit and push branches
- create/update PRs
- rerun/watch CI and make CI repair commits until green

Permissions not granted:
- merge
- close
- release
- destructive cleanup
- unrelated workflow/secret changes
- work outside this repository

Stop and ask Bram when:
- required permission is missing
- access, live proof, or a waiver is needed
- the next action is land, delete, merge, close, or release
- the repository checkout is unsafe for branch work

Output: start with the ledger path, resolved GitHub repository, permissions accepted, and first selected item URL. Status reports use Active, Needs Bram, and Ready next.
