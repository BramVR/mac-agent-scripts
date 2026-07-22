# Session findings

Evidence distilled from prior Codex tasks in `mac_maya_dev`, July 2026.

## Verified successful shape

1. Canonical config from `/Users/bram/Projects/mac_maya_dev/.maya-dev.toml`.
2. Read-only `windows check`; interactive user logged in; configured task Interactive/Ready; 7002 free or correctly Maya-owned; Maya 2025 isolated on 7001.
3. Current immutable GG_MayaMCP deployment selected.
4. One scheduled-task start through `MayaDevSessiond2024`.
5. Wait through the 180-second readiness budget, then inspect status before retrying.
6. Accept only `running` + successful `scene.info` + green doctor.
7. Use sessiond `call`/MayaMCP for scene actions; SSH only for lifecycle/diagnostics.

Live compatibility proof after the Maya 2024 fixes:

- Maya 2024 reached `running` on `127.0.0.1:7002`.
- Full-capacity commandPort probe passed.
- `scene.info` returned valid data through `daemon_worker`.
- Isolated Maya 2025 proof succeeded on its unchanged path.
- Final cleanup/restoration left the production 7001 session/task unchanged.

## Repeated failure causes

### Wrong host/router

Agents invoked `hermes-win`, then discovered the Maya workstation was actually `maya-win`. This wasted diagnostics and risked touching an unrelated automation host. Maya work always uses `maya-win` directly.

### Worktree config assumption

Codex worktrees lacked `.maya-dev.toml`; the canonical main checkout had the valid ignored config. Use the absolute canonical config instead of inventing a worktree copy.

### Offline/unlocked desktop

SSH timed out while the PC was asleep/offline. The correct response was one bounded probe, then ask Bram to wake/unlock/log in. Interactive scheduled-task starts require the configured Windows user to be logged in.

### Local environment gate

One run failed GG_MayaMCP mypy because dependencies were absent; `uv run` also created an untracked `uv.lock`. Run source checks only when deploying changed source. Preserve unrelated/untracked files.

### Oversized Windows commands

Deploy finalization and interactive start exceeded Windows command-line limits. `mac_maya_dev` commits `12ac230` and `dd89b10` moved oversized PowerShell through SSH stdin. Use a checkout containing those fixes or later.

### Atomic deployment selector

Some deploys uploaded a correct immutable snapshot but failed replacing an existing `current.json` through `File.Replace`. Manual selector edits made later tasks harder to reason about. Treat this as a repository bug; do not bypass atomic selection.

### Stale scheduled-task launcher

Maya launched through an older compatibility task and the worker never became ready. `windows setup --apply` repaired the repository launcher/task and its post-check passed. Preview first; apply only the configured repair.

### Maya 2024 commandPort compatibility

Maya 2024 listened on 7002 but returned zero bytes with `echoOutput=True`; framing variations and `securityWarning=False` did not fix it. The verified fix was exact-2024 policy: echo disabled plus the structured/base64 response path and larger buffer/full-capacity probe. GG_MayaMCP 0.6.0 and the matching sessiond compatibility policy proved this live. Do not revive the disproven security-warning theory.

### Startup timeout race

The `start` command sometimes timed out just before sessiond reached `running`. A later status showed daemon, Maya, MCP, and call server healthy. Poll status and call `scene.info` before restarting.

### Scripting bypasses

Tasks manually replaced `current.json`, changed generated launchers, or registered temporary scheduled tasks to add raw execution. These paths were fragile and required restoration. Express `--mcp-script-dirs` and `--mcp-enable-raw-execution` through the managed launcher/configuration instead.

### Reopen/script-node hang

An embedded controller-builder script node ran on reopen and left Maya listening but unresponsive. Save before scripting; prefer approved explicit scripts; test reopen in a controlled stage; avoid auto-executing build script nodes.

## Maya use findings

- Query the tool catalog after connection; do not assume raw execution or an approved script directory.
- Direct tool actions provided the clearest visible modeling/rigging progress.
- Use bounded scripts for missing high-level operations, repetitive validation, or persistent solver logic—not a complete hidden build.
- Continuous playblast sometimes evaluated scripted rigs stale. For proof, use separate set-time, viewport refresh, and capture actions at representative frames. Do not accept a generated capture without visually inspecting it.
