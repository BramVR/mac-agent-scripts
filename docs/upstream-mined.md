# Upstream mining marker

- Reviewed `upstream/main` through: `0798fed56f5a059e988cddcf068ea19969ad7275` (2026-07-21, reviewed 2026-07-23)
- Full classification report of that pass: 232 commits → 19 groups already present, 12 skip (Peter-personal), 19 port candidates, 2 preserved-skill conflict families (autoreview, maintainer-loop). Port candidates pending Bram triage.

## Flow (repeat per pass)

```bash
cd ~/Projects/agent-scripts && git fetch upstream
git log --reverse <marker-sha>..upstream/main
```

Delegate classification to Codex ($codex-first): buckets = already-present / Peter-personal skip / port candidate / touches preserved skills (never blind-port those). Port selectively via /tmp staging (AGENTS.MD rule). Practice-revealing changes also go to the vault as claims on `Sources/2026-07-22 steipete agent-scripts.md` (SHA = evidence, commit date = published). Update the marker SHA here after each pass.
