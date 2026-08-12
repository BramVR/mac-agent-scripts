---
name: maya-plugin-manual
description: "Open or refresh one persistent interactive Maya session with an exact plug-in build and its Python tool paths ready for hands-on testing. Use for clean Maya handoffs, latest plug-in manual testing, or requests to leave a Maya plug-in UI open for the user."
---

# Maya Plugin Manual Session

Prepare a long-lived artist session, not an acceptance run. Use `$maya-plugin-e2e` for immutable proof runs and `$maya-dev` only for its fixed Maya 2024 development route.

## Invariants

- End with exactly one `maya.exe` for the requested Maya version.
- Never start a Maya Stall Fresh Run for a manual handoff. Its wrapper restores `sys.path` and removes run-scoped modules after execution; a UI may appear healthy and later fail lazy imports.
- Use the existing managed `gg_mayasessiond` broker directly. Start its configured interactive task once only when stopped.
- Check the Maya Stall Host Lock before lifecycle changes. If another run owns it, stop and report the owner. Do not compete.
- Stage the exact plug-in artifact under the configured trusted plug-in root. Stage source under a unique persistent directory allowed by the broker's `script.execute` policy.
- Do not read or print broker state files or call tokens.
- Leave a successful requested session running.

## Prepare

1. Read repo instructions and its Maya/E2E docs.
2. Resolve the requested revision. For “latest,” use the latest successful target-branch CI artifact, not an ignored local binary. Record commit, job, version, size, and SHA-256.
3. Read only the needed host-config fields: host, Maya version, work root, trusted artifact root, broker Python/repo/state directory, recovery task. Never dump the config.
4. Inspect, without mutation:
   - Host Lock state;
   - scheduled-task state;
   - `maya.exe` count, PID, version, and creation time;
   - broker status through `gg_maya_sessiond.cli status`.
   Capture raw broker status inside the remote shell and emit only status plus
   process-health fields. Raw status JSON may contain a call token.
5. Reuse one healthy matching manual session when its artifact and source identities match. A previously handed-off session is artist-owned even when the broker recognizes it. Stop a mismatched session only when process metadata and this task's records prove it was launched by the current task and has not been handed off; otherwise preserve it and ask Bram before closing it. Never kill an unknown Maya process.

## Stage

Create one unique remote manual root under the broker-allowed runs directory, keyed by project and commit, for example:

```text
C:/maya-stall/runs/manual-<project>-<short-commit>/
  src/
  setup.py
  ready.json
```

Stage source from an archive of the exact resolved commit, or an equivalent explicit tracked-file allowlist, without modifying the local checkout. Never recursively copy the working tree: exclude ignored and untracked files, and preserve symlinks as links rather than dereferencing them. Copy the binary to its project-relative destination beneath `trustedPluginArtifactsRoot`. Verify remote binary size and SHA-256 equal the downloaded artifact before loading.

## Launch once

1. Recheck Host Lock and matching Maya process count.
2. If broker status is healthy, reuse it. If stopped and Maya count is zero, start the configured interactive recovery task once. Do not follow this with `maya-stall run`.
3. Poll broker status for at most 60 seconds. Do not issue a second start while status is `starting` or the task is running.
4. Require one matching `maya.exe`, healthy broker/MCP, and the expected Maya build.
5. Invoke the staged setup through the broker's direct `script.execute` call. The setup must:
   - refuse a non-empty scene unless the user explicitly requested reuse;
   - unload only an auto-loaded copy of the target plug-in;
   - load the exact trusted artifact and verify its path/version;
   - permanently prepend the staged source root to both `sys.path` and `PYTHONPATH` in the Maya process;
   - clear only the product's Python modules, then explicitly import every required package root, including lazy roots such as `rig`;
   - open and raise the real tool UI;
   - write `ready.json` only after imports succeed and the window is visible.

Use the configured broker Python and repo for calls; let `--state-dir` resolve authentication internally. Never inline or inspect a call token.

## Verify before handoff

Read the non-secret `ready.json`, then prove:

- one matching `maya.exe` exists;
- plug-in path is beneath the trusted root;
- plug-in version and SHA-256 match the target artifact;
- `sys.path` and `PYTHONPATH` contain the persistent staged source root;
- required package roots import from that source root;
- scene is untitled and empty;
- tool window is visible.

Capture one private screenshot only when useful, inspect it for duplicate Maya windows and error dialogs, and do not publish it without a confidentiality check. If any check fails before handoff, stop only the session proven to have been launched by this task, then fix the setup before relaunching. After handoff, preserve the artist-owned session and ask Bram before closing it. Never stack another Maya process on top.

## Handoff

Report Maya version, plug-in version/commit, source root, process count, UI state, and whether Maya remains open. State that this is a manual session, not acceptance evidence.
