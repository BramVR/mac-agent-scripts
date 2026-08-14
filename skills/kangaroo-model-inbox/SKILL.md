---
name: kangaroo-model-inbox
description: "Operate the local Kangaroo Maya model-check inbox: scan a Drive folder once, inspect watcher status and reports, diagnose failed checks, or prepare a Windows scheduled watcher. Use for incoming Maya ASCII .ma model deliveries that must run through Maya 2022, Maya Stall, gg_kangaroobuilder_core, and the gg_kangaroo_buildscripts sanity checker."
---

# Kangaroo Model Inbox

Operate the deterministic folder worker in `gg_kangaroo_buildscripts`. Keep the
always-running monitor in Windows Task Scheduler; use this skill as its control
and reporting layer.

## Resolve the local setup

1. Use `$env:KANGAROO_BUILDSCRIPTS_REPO` when set; otherwise try
   `C:\PROJECTS\GG\gg_kangaroo_buildscripts`.
2. Read `docs/maya-stall-sanity.md` before changing or running the workflow.
3. Require these existing paths:
   - `scripts/model_inbox.py`
   - `scripts/run-model-sanity.ps1`
   - the Maya Stall executable from `$env:KANGAROO_MAYA_STALL`
   - the host config from `$env:KANGAROO_MAYA_HOST_CONFIG`
   - the inbox from `$env:KANGAROO_MODEL_INBOX`
4. If an environment variable is missing, discover a safe existing local path.
   Ask the user only for a missing inbox or host-specific path that cannot be
   determined without guessing.

## Choose the operation

### Check once

Run from the build-scripts repository:

```powershell
py -3.11 .\scripts\model_inbox.py once `
  --inbox $env:KANGAROO_MODEL_INBOX `
  --maya-stall $env:KANGAROO_MAYA_STALL `
  --host-config $env:KANGAROO_MAYA_HOST_CONFIG
```

Report which models were skipped, passed, failed model checks, or hit an
infrastructure error. A failed model check is a completed check, not a worker
crash. For each attempted model, use the ledger record's `htmlReport` as the
canonical report and give the user its full local path.

### Show status or the newest report

Run the worker with `status`. It reads the trusted ledger from the default
`%LOCALAPPDATA%\KangarooModelInbox\<inbox-id>` state root and prints that path
plus `latestReport`. Resolve `latestReport` under `<inbox>/_model-checks/` and
use that stable `report.html` for every user-facing report request. If the
field is absent in an older ledger record, fall back to
`<inbox>/_model-checks/<reportDirectory>/report.html`, then inspect the
referenced `scenarioResult` only when deeper diagnosis is needed. Summarize the
complete `checkResults` list with an OK or Needs attention outcome for every
sanity check, then fatal findings, advisory findings, Maya version, Kangaroo
core commit, and the checked-model/report paths in plain English. Treat a
missing `checkResults` field as legacy evidence rather than assuming omitted
checks passed.

### Watch continuously

Use the `watch` mode only when the user explicitly asks to start or install the
persistent watcher. Prefer Windows Task Scheduler under the logged-in artist
account. Maya requires the interactive desktop. Do not keep a Codex task alive
as the monitoring mechanism.

Use the same arguments as `once`, replacing the mode with `watch`. Keep one
watcher per inbox.

### Retry

Infrastructure errors are eligible on the next scan. Models with completed
`passed` or `failed` Scenario Results are keyed by source path and content hash;
they run again automatically after their contents change. Do not delete a
completed ledger record merely to force a rerun unless the user explicitly
requests it.

## Safety rules

- Accept only top-level `.ma` files. Do not process `.mb` files.
- Never edit, rename, move, or delete the delivered source model.
- Keep Maya 2022 on the dedicated `local-maya-2022` profile, state directory,
  and port. Never stop or reuse an unrelated Maya 2025 session.
- Run one model check at a time and let Maya Stall own the host lock and exact
  session cleanup.
- Keep the ledger and process locks in the default local state root, outside the
  shared inbox. Never put `--state-root` inside the Drive folder.
- Treat `_model-checks`, `.maya-stall`, dependencies, input models, and evidence
  as local runtime data; do not commit them.
- Treat the canonical HTML as untrusted local evidence. Do not copy raw model
  contents into it, and preserve HTML escaping when changing report generation.
- Do not enable Kangaroo native plug-ins for this checker workflow.
- Before a real run, confirm `.kangaroo-core-commit` exists in the local
  dependency. If missing, run `scripts/sync-kangaroo-core.ps1` against the
  local `gg_kangaroobuilder_core` checkout.
