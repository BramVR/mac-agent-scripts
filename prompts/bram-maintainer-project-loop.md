---
summary: "Start one Bram maintainer loop for a project."
read_when:
  - Starting a delegated maintainer loop for one repository.
---

# Bram Maintainer Project Loop

Use $bram-maintainer-loop for <repo-or-owner/repo>.

Objective: run one project maintainer loop until autonomous queue work is exhausted or a Bram decision is required.

Scope: only <repo-or-owner/repo>. Use the skill's repository resolution, worker, proof, and reporting rules.

Codex automation expectation: this is a Codex self-monitoring automation, not a one-shot task. At startup, create or update one Codex heartbeat automation attached to this coordinator thread, scheduled to wake every 5 minutes. The heartbeat should refresh coordinator, worker, PR, and CI state; continue the loop; and close out only at a blocker, permission boundary, no safe work remains, or stable decision-ready state for work that cannot be merged under current permissions. Do not stop at a green mergeable loop PR; merge it when gates pass, then continue. Keep in-turn timed poll cycles running while active. Do not rely on Bram to ask for status, done, or check-in prompts. Do not send a final answer while delegated workers, required CI, or authorized repair loops are still active.

Permissions granted:
- triage and monitor
- create/update the coordinator heartbeat automation
- create/rename worker threads
- implement autonomous issues/PRs
- create focused branches
- commit and push branches
- create/update PRs
- rerun/watch CI and make CI repair commits until green
- merge loop-prepared PRs after required proof, autoreview, confidentiality gate, and green CI

Permissions not granted:
- close
- release
- destructive cleanup
- unrelated workflow/secret changes
- work outside this repository

Stop and ask Bram when:
- required permission is missing
- access, live proof, or a waiver is needed
- the next action is delete, close, release, or a merge whose required gates are not satisfied
- the repository checkout is unsafe for branch work; clean Codex worktree detached HEAD is acceptable if `origin/main` resolves and a focused branch can be created from it

Output: start with the ledger path, resolved GitHub repository, permissions accepted, and first selected item URL. Status reports use Active, Needs Bram, and Ready next.
