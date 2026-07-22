---
name: maya-dev
description: "Launch, reconnect, diagnose, and use Bram's managed Maya 2024 + GG_MayaMCP development session from macOS through mac_maya_dev, mayasessiond, SSH alias maya-win, and loopback port 7002. Use for Maya modeling/rigging tasks, MayaMCP scene work, Maya startup failures, stale managed sessions, deployment selection, approved/raw scripting configuration, or verifying the Mac-to-Windows Maya tool chain."
---

# Maya Dev

Use the managed `mac_maya_dev` path. Keep Maya on the interactive Windows desktop and MCP beside Maya; carry control over SSH.

## Fixed routing

- Use `/Users/bram/Projects/mac_maya_dev` as the CLI checkout and its ignored `.maya-dev.toml` as the canonical config.
- A Codex worktree normally has no `.maya-dev.toml`; do not copy or invent one there.
- Use SSH alias `maya-win`. Never invoke or route through `hermes-win` for Maya work.
- Use Maya 2024, `MayaDevSessiond2024`, and loopback port `7002`.
- Leave Maya 2025, port `7001`, `MayaStallSessiondUI`, credentials, network, firewall, and unrelated sessions untouched.
- Treat the shared Maya host as single-owner. When task-list tools exist, check for another active Maya task before lifecycle changes. Never compete for port 7002.

## Start or reconnect

1. Read the current repository `README.md` and `.maya-dev.toml` keys. Do not print secrets or sessiond call tokens.
2. Inspect, in this order:

   ```sh
   cd /Users/bram/Projects/mac_maya_dev
   uv run maya-dev --config .maya-dev.toml --json windows check
   uv run maya-dev --config .maya-dev.toml --json status
   ```

   `status` returning nonzero for `stopped` or `failed` is state evidence, not a reason to abandon the workflow.

3. If status is `running`, prove the existing session before changing anything:

   ```sh
   uv run maya-dev --config .maya-dev.toml call scene.info
   uv run maya-dev --config .maya-dev.toml status
   uv run maya-dev --config .maya-dev.toml doctor
   ```

   Reuse it when all three pass. Do not restart a healthy session.

4. If status is `starting`, wait and poll status. Do not issue another start.
5. If stopped/failed and the selected MCP snapshot is current, run one start:

   ```sh
   uv run maya-dev --config .maya-dev.toml start
   ```

6. A `start` timeout can occur just before the worker reaches `running`. Before any retry, poll `status` for up to 60 seconds and try `scene.info` once if status becomes running.
7. Accept readiness only when `scene.info`, `status`, and `doctor` pass and port 7002 is loopback-owned by configured Maya 2024.

For the standard path, prefer `scripts/launch.sh`. Add `--deploy` only when GG_MayaMCP source changed and the session is not running. Use `--dry-run` to inspect its commands.

## Deploy only when needed

When GG_MayaMCP source changed:

```sh
uv run maya-dev --config .maya-dev.toml check
uv run maya-dev --config .maya-dev.toml deploy
```

- Preserve immutable deployments; let `deploy` select `current.json`.
- Do not hand-edit remote `current.json`, patch the scheduled task, or launch Maya as an SSH child.
- If deploy uploads the snapshot but atomic `current.json` replacement fails, stop. This is a `mac_maya_dev` deploy bug; fix it in the repository rather than bypassing the selector.
- If check/setup reports task-launcher drift, run `windows setup` as a read-only preview. Apply once only when the plan contains the expected configured launcher/task repair and no blockers.

## Use MayaMCP

Inventory before scene work:

```sh
uv run maya-dev --config .maya-dev.toml call --list
uv run maya-dev --config .maya-dev.toml call scene.info
```

Use MayaMCP tools as the scene-control plane. Use SSH only for managed lifecycle and diagnostics. Build in visible, meaningful stages; save after major milestones.

Use higher-level tools first. For Python:

1. Prefer `script.list` and `script.execute` with configured `MAYA_MCP_SCRIPT_DIRS`.
2. Use raw `script.run` only when the request needs it and the managed session was deliberately launched with `--mcp-enable-raw-execution`.
3. Treat script/raw support as launch-time configuration. Do not create a temporary scheduled task or modify the installed launcher/current selector ad hoc. If `mac_maya_dev` cannot express the required flags, implement that support there first.
4. Keep scripts bounded and staged. Never hide the whole scene build behind one monolithic script.
5. Save before risky script or reopen operations. Avoid auto-running script nodes that can hang Maya during file open.

## Recovery discipline

- Do not repeat identical failed calls.
- Make at most two evidence-based recoveries for one failure class.
- On SSH timeout: stop and ask Bram to wake/unlock/log into `maya-win`; do not loop.
- On `scene.info: Empty response`: verify deployed MCP/sessiond compatibility. Maya 2024 requires the released 2024 commandPort compatibility path; `securityWarning=False` was a disproven fix.
- On CLI timeout with Maya/7002 alive: inspect status/logs and wait; do not kill the late-starting worker.
- On stale task action/launcher: use `windows check` and setup preview, then the configured repair path.
- On unresponsive Maya after scene scripting: preserve the last saved scene, restart only the managed Maya 2024 session, and reopen with unsafe script-node execution disabled when applicable.
- Read [references/session-findings.md](references/session-findings.md) when diagnosis is needed.

## Finish

Report:

- sessiond/Maya/MCP health;
- Maya PID/session and loopback port evidence without secrets;
- deployed source identity when changed;
- `scene.info` proof;
- scene/artifact paths;
- whether Maya remains open.

Leave a successful requested Maya session running unless the user asks to stop it.
