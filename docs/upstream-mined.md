# Upstream mining marker

- Reviewed `upstream/main` through: `6878dd818b34659a925ec45fb7225a81b6a5c69a` (2026-07-22, reviewed 2026-07-23)
- Full classification report of the 232-commit pass (through `0798fed`): 19 groups already present, 12 skip (Peter-personal), 19 port candidates, 2 preserved-skill conflict families (autoreview, maintainer-loop). Port candidates pending Bram triage.
- 2026-07-23 pass (`0798fed..6878dd8`, 1 commit): ported codex-first git-mechanics mandate, guarded CI waits, fresh work-order sessions, AGENTS.md-only rule; scrubbed openclaw watcher example + CLAUDE.md-symlink claim; kept Bram divergences (no fast_mode, loopback-only gate, short description, `$bram-maintainer-loop-v2` pointer).
- 2026-08-19 targeted refresh: mined `skills/browser-use` through `2e320ff086cfc82d01037edab0683857d48c1698`; combined current relay hardening with Bram's cmux-first route. Global marker unchanged because this was not a full upstream classification pass.
- 2026-09-01 targeted PStack pass: mined `cursor/plugins` `pstack` at `b9ddc83c32972210b8a94d389130713e8eed346e`; ported `principle-build-the-lever` and `principle-prove-it-works` with Codex metadata and explicit invocation. Existing `architect`, `blast-radius`, and `unslop` retained; Cursor-cloud orchestration and broad persona skills skipped. Global marker unchanged because this was a separate upstream.
- 2026-09-03 targeted PStack pass: mined `cursor/plugins` `pstack` at `b9ddc83c32972210b8a94d389130713e8eed346e`; ported 21 principle skills, Poteto Mode, and supporting workflows with Codex collaboration, permission, transcript, and model-routing adaptations. Global marker unchanged because this was a separate upstream.

## Flow (repeat per pass)

```bash
cd ~/Projects/agent-scripts && git fetch upstream
git log --reverse <marker-sha>..upstream/main
```

Delegate classification to Codex ($codex-first): buckets = already-present / Peter-personal skip / port candidate / touches preserved skills (never blind-port those). Port selectively via /tmp staging (AGENTS.MD rule). Practice-revealing changes also go to the vault as claims on `Sources/2026-07-22 steipete agent-scripts.md` (SHA = evidence, commit date = published). Update the marker SHA here after each pass.
