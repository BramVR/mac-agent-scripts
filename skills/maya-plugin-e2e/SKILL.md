---
name: maya-plugin-e2e
description: "Maya plugin UI/e2e proof workflow: use when testing Maya plugins through Maya Stall, Windows Maya hosts, pluginArtifacts, screenshots/recordings, Scenario Result JSON, untrusted-plugin popups, UI clicking, or PR closeout gates that need real Maya evidence."
---

# Maya Plugin E2E

## Overview

Run real Maya plugin proof without rediscovering the same traps. Prefer deterministic setup, trusted plugin staging, explicit UI actions, and evidence-backed closeout over manual smoke claims.

## Fast Path

1. Confirm target commit, CI artifact job, artifact size, and plugin hash before touching the live host.
2. Confirm the Maya Stall host is free, the run command, host config, and target profile.
3. Verify `pluginArtifacts` are declared by the scenario/project and the host config has a trusted plugin artifact root.
4. Start from a clean run workspace; do not reuse stale screenshots, recordings, or Scenario Results.
5. Run the real gate through `maya-stall run`, not manual Maya unless explicitly debugging.
6. Inspect Scenario Result JSON first, then screenshots/recordings, logs, and saved scene.
7. Close only with exact-head proof: commit, CI artifact job/id/hash/size, run id, screenshot/recording paths/sizes, Scenario Result fields, confidentiality pass.

## Consuming Repo Contract

Do not create a project-specific copy of this skill. Make each consuming repo
own the deterministic test inputs:

- `.maya-stall.yaml` with named Scenario, `pluginArtifacts`, Maya scripts,
  expected outputs, Visual Evidence, and Validators;
- a checked-in Maya script that drives real product controls and writes the
  Scenario Result;
- a short repo doc with exact build, artifact download, `plan`, `doctor`, and
  `run` commands;
- an `AGENTS.md` route to this skill and the repo doc.

Keep Host Config outside the repo. Prefer a stable operator-owned path such as
`~/.config/maya-stall/hosts.yaml`, selected through `MAYA_STALL_HOST_CONFIG`.
The skill owns the workflow; the consuming repo owns product assertions; the
host config owns private infrastructure and trust policy.

## Preflight

Use exact queries; do not print secrets or full host configs.

```bash
maya-stall status
python3 - <<'PY'
import json, pathlib, zipfile, hashlib
artifact = pathlib.Path("artifacts.zip")
print("artifact:", artifact.resolve())
print("artifact_size:", artifact.stat().st_size)
print("artifact_sha256:", hashlib.sha256(artifact.read_bytes()).hexdigest())
with zipfile.ZipFile(artifact) as z:
    for name in z.namelist():
        if name.lower().endswith((".mll", ".so", ".bundle", ".dll")):
            data = z.read(name)
            print("plugin:", name)
            print("plugin_size:", len(data))
            print("plugin_sha256:", hashlib.sha256(data).hexdigest())
PY
```

For Maya Stall host config, report only safe shape:

```bash
python3 - <<'PY'
import json, pathlib
try:
    import yaml
except Exception:
    raise SystemExit("Install/read yaml another way; do not dump host config.")
p = pathlib.Path("/path/to/hosts.yaml")
data = yaml.safe_load(p.read_text())
hosts = data.get("hosts") or []
for i, h in enumerate(hosts):
    safe = sorted(k for k in h if k.lower() not in {"host","hostname","user","username","identityfile","password","privatekey"})
    print(f"host[{i}] keys:", safe)
    print(f"host[{i}] trustedPluginArtifactsRoot:", bool(h.get("trustedPluginArtifactsRoot")))
PY
```

If `trustedPluginArtifactsRoot` is missing and the plugin loads from a transient workspace path, expect Maya's security modal. Fix trusted staging before rerun; clicking `Allow` is a diagnostic escape hatch, not accepted proof.

## Running

Use the project-provided command exactly when a coordinator gives one:

```bash
/tmp/maya-stall-latest run --host-config /tmp/hosts.yaml --target-profile default --stop-after never product_ui_e2e
```

During a live run:

- Do not start a second live run against a shared host.
- Watch for timeout text, Scenario Result path, run id, artifact bundle root, screenshot path, and recording path.
- If the command times out, immediately inspect the captured failure screenshot before editing code.
- If the screenshot shows a Maya modal, identify the modal; do not assume the scenario is slow.
- If the screenshot shows no modal and Maya is active, inspect script logs and outputs for waiting loops, expensive meshes, missing file writes, or stuck UI callbacks.

## UI Proof

For behavior-changing plugin PRs, require real UI operations that would fail if controls or windows are broken:

- Create representative geometry, not a trivial plane, when the behavior is surface-dependent.
- Open the plugin's real UI windows in the same Maya session.
- Position windows before screenshot/recording; verify bounding boxes do not overlap.
- Click or call through the actual UI control callbacks used by artists.
- Assert resulting node attributes or state changed to the expected values.
- Sample geometry before/after deformation; fail on zero or tiny displacement.
- Save the scene and include the saved path in Scenario Result JSON.

Common KLV Push/Dynamics expectations:

- Curved high-resolution target, e.g. `polySphere` or body-like mesh.
- KLV Push UI controls: firmness/depth/bulge or project-equivalent real artist controls.
- KLV Dynamics window in the same session when the PR touches shared product UI.
- Scenario fields: `targetSurface`, `windowsNonOverlapping`, `deformationSamples`, `savedScene`.

## Screenshot/Recording Points

Capture or verify evidence at these points:

- Startup failure: immediate failure screenshot, useful for modals/popups.
- After plugin load: UI windows visible, no security modal.
- After control edits: changed controls visible where possible.
- After deformation: viewport shows changed target.
- Final closeout: Scenario Result references screenshot/recording/saved scene or the evidence bundle contains them.

Before publishing evidence paths or attaching media, inspect for private desktop content, hostnames, secrets, chat/browser tabs, or personal files. If screenshots include private content, keep them local and report only non-sensitive metadata unless the coordinator explicitly approves publication.

## Popup Handling

Treat recurring popups as setup failures first:

- `Untrusted Plugin Loading`: verify `pluginArtifacts` and `trustedPluginArtifactsRoot`; rerun from trusted staging. Do not close issue by clicking `Allow`.
- Missing plugin/load failure: verify downloaded artifact commit/job, extracted plugin extension, `MAYA_PLUG_IN_PATH`, and Scenario Result logs.
- License/update/welcome dialogs: close only if they are host baseline noise; then rerun from a clean state and record the action.
- File overwrite/save dialogs: make scenario write to a unique run path or remove the prompt condition in code.

Only use manual clicks to diagnose or clear host baseline state. Accepted proof must be repeatable from the command line.

## Failure Triage

Classify before patching:

- Scenario-owned: too slow mesh, waits on missing output, no timeout budget awareness, non-unique files, UI overlap, callback not invoked, no final JSON.
- Host/Maya Stall owned: SSH/session timeout before scenario starts, broken screenshot/recording transport, missing trusted root in host config, broker unreachable.
- Artifact-owned: stale commit artifact, wrong Maya version, missing plugin binary, bad hash/size mismatch.

If scenario-owned, patch the same PR/MR and rerun local tests, autoreview, CI, artifact download, then real live gate. If host/Maya Stall owned and independent of the scenario, open/propose separate infra work and do not merge on waived proof.

## Closeout Checklist

Record concise proof:

- target commit and target branch
- CI pipeline/job id, artifact size, artifact sha256, plugin sha256
- Maya Stall command, run id, Maya version/profile
- Scenario Result path and key fields
- screenshot path/size and recording path/size
- saved scene path/size
- local tests and autoreview result
- Public Artifact Confidentiality: PASS/FAIL with reason

Never close a behavior-changing Maya plugin PR with fake/local-only, stale-head, plane-only, skipped, manual-only, or screenshot-only proof.
