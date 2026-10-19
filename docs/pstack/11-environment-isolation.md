---
summary: "Separate T3 plugin pstack from personal terminal skills."
read_when:
  - "Configuring T3 provider skill visibility or changing pstack presets."
---

# Isolate T3 skills from terminal sessions

T3 uses the plugin's namespaced pstack skills. Terminal sessions use the personal pstack skills. Custom skills such as `autoreview` and `hermes-win` stay available in both environments. Keep the skill symlinks stable so simultaneous sessions cannot switch each other's skills.

Set the per-provider **Launch arguments** in T3's **Settings > Providers**:

- Codex: paste [codex-t3-launch-args.txt](../../config/t3-pstack/codex-t3-launch-args.txt). It enables `t3-pstack@t3-pstack` and disables the personal pstack skills by their canonical `SKILL.md` paths.
- Claude: use `--settings /Users/bram/Projects/agent-scripts/config/t3-pstack/claude-t3-settings.json`. [That settings file](../../config/t3-pstack/claude-t3-settings.json) enables the plugin and hides the overlapping personal skill names with `skillOverrides`.

The Codex preset contains absolute paths for this checkout, including an extra local `teach` copy. Regenerate its paths if the checkout moves or personal pstack copies change. Review both presets after a pstack update adds or renames skills.

Verify a fresh T3 runtime advertises `t3-pstack:poteto-mode`, hides bare `poteto-mode`, and retains custom skills. A saved launch argument alone is insufficient proof. Current provider processes can retain their earlier launch configuration; reload T3 when those processes do not use the saved arguments. Coordinate a reload with other running chats.

Only after that T3 check passes, disable `t3-pstack@t3-pstack` in each harness's normal user configuration. For Codex, set `enabled = false` under `[plugins."t3-pstack@t3-pstack"]` in `~/.codex/config.toml`. For Claude, run `claude plugin disable t3-pstack@t3-pstack --scope user`. T3's launch overrides enable it for T3 sessions. Verify a fresh terminal session has personal pstack, no plugin pstack, and custom skills.

Codex's CLI override key is `plugins.t3-pstack@t3-pstack.enabled=true`, without embedded quotes around the plugin ID. The CLI splits the key on dots; TOML table-header quoting does not apply there.

