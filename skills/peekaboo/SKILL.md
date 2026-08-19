---
name: peekaboo
description: "Peekaboo v4 macOS screenshots, inspection, and UI automation."
---

# Peekaboo

Use Peekaboo v4 for native macOS capture, Accessibility inspection, and UI automation. Prefer exact background delivery so the user's foreground app, keyboard focus, and physical cursor stay untouched.

_Source: [openclaw/Peekaboo v4.2.0](https://github.com/openclaw/Peekaboo/releases/tag/v4.2.0), signed release and v4 command contract._

## Resolve the binary

Prefer `peekaboo` on `PATH`. Bram's release install lives in `~/.local/bin`, which precedes Homebrew. Check the selected binary before relying on syntax:

```bash
PB="${PEEKABOO_BIN:-$(command -v peekaboo || true)}"
[ -x "$PB" ] || { echo "peekaboo missing"; exit 1; }
"$PB" --version --json
```

Require major version 4. Version 3 used removed commands such as top-level `list`, `image`, `hotkey`, and `click --coords`.

## Runtime host and permissions

- Use `bridge status --verbose --json` to see whether Peekaboo selected its reusable daemon, GUI Bridge, or local runtime.
- Check `permissions status --all-sources --json`. Grant Screen Recording, Accessibility, and Event Synthesizing to the selected runtime source, not merely to the invoking terminal.
- When an installed `Peekaboo.app` must provide the GUI Bridge, launch it without focus using `open -gj -a Peekaboo`, then confirm the selected socket and `hostKind`.
- Prefer Bridge capture from SSH, LaunchAgents, Codex, and other background sessions. `--no-remote` is a local-debug override, not the default proof path.
- Never run an unsigned or ad-hoc build against saved TCC or Keychain state.

## v4 command names

- Inventory: `app list`, `window list`, and `screen list`.
- Screenshots and visual maps: `see`.
- Accessibility-only inspection: `see --tree --no-screenshot`.
- Standalone keys and chords: `press`.
- Named Accessibility actions: `action`.
- Coordinate clicks: `click --at x,y`.
- Drags: `drag --from x,y --to x,y`.
- Stable postconditions: `verify` instead of fixed sleeps.

Use `tools --json`, `tools describe <name> --json`, `learn`, and `<command> --help` when the command surface matters.

## Background-first safety

- Supply an exact `--app`, `--pid`, `--window-id`, or fresh snapshot target for mutations.
- Keep background delivery as the default. Add `--foreground` only when the user authorized focus or shared-pointer interaction, or when the target demonstrably rejects background delivery.
- Shared-cursor and targetless global input require explicit foreground mode. This includes `move`, `drag`, targetless or smooth scrolling, targetless keyboard input, and long-press clicks.
- Do not click, type, paste, quit, move, resize, or otherwise mutate UI unless the user asked or the target is a controlled test.
- Re-observe after every mutation. Never replay an indeterminate action blindly.
- Treat element IDs as opaque and valid only for the captured state. Use a new `see` after navigation or re-rendering.

## Common commands

```bash
"$PB" permissions status --all-sources --json
"$PB" bridge status --verbose --json

"$PB" screen list --json
"$PB" app list --include-hidden --include-background --json
"$PB" window list --app Safari --json

# Screenshot only.
"$PB" see --no-elements --mode screen --path /tmp/screen.png --json

# Visual map with element IDs and snapshot ID.
"$PB" see --app Safari --annotate --path /tmp/safari-see.png --json

# Accessibility tree without pixels.
"$PB" see --app Safari --tree --no-screenshot --json

# Use IDs and snapshot from a fresh observation.
"$PB" click --on "$ELEMENT_ID" --snapshot "$SNAPSHOT_ID" --json
"$PB" action AXPress --on "$ELEMENT_ID" --snapshot "$SNAPSHOT_ID" --json

# Process-targeted background keyboard delivery.
"$PB" type "text" --app TextEdit --json
"$PB" press Return --app TextEdit --window-id 1234 --json
"$PB" paste "text" --app TextEdit --json

"$PB" verify --app Safari --window-exists --timeout 2s --json
"$PB" tools --json
```

## Click coordinates safely

Screenshot pixels are not click coordinates. `click --at` uses logical points. With target flags, coordinates are relative to the resolved window. Without a target they are global screen coordinates. Add `--global` when targeted coordinates must remain screen-global.

A background coordinate click requires a fresh exact-window snapshot:

```bash
"$PB" window list --app Safari --json
"$PB" see --app Safari --window-id 12345 --path /tmp/safari.png --json
"$PB" click --window-id 12345 --at 20,40 --snapshot "$SNAPSHOT_ID" --json
```

Peekaboo revalidates the captured process generation, window ID, and bounds before dispatch. If it cannot establish an exact receipt, let the command fail. Do not guess or silently promote to foreground mode.

For element work, prefer IDs from a fresh `see` and pass the snapshot explicitly. After an action changes UI, capture a new snapshot.

## Input strategies

Use these only when diagnosing delivery paths:

- `--input-strategy actionOnly` proves live Accessibility re-resolution and action invocation.
- `action AXPress` is the cleanest direct Accessibility smoke test.
- `--input-strategy synthOnly` proves coordinate resolution and event delivery, but requires an independent state check.
- Coordinates cannot use `actionOnly`.

## Workflow

1. Resolve the v4 binary and record its version.
2. Check the selected runtime host and permissions.
3. Resolve the target with `app list` or `window list`; prefer PID or window ID for exact mutation.
4. Observe with `see --no-elements`, ordinary `see`, or `see --tree --no-screenshot`.
5. Interact in the background with an exact target and fresh snapshot.
6. Verify every mutation with a new observation or `verify` predicate.
7. Use explicit foreground mode only for authorized shared cursor or confirmed application limitations.
8. Verify image artifacts with `sips -g pixelWidth -g pixelHeight <path>` or view them locally.

Source of truth: live help plus the [Peekaboo command docs](https://github.com/openclaw/Peekaboo/tree/main/docs/commands). When copied examples and live help disagree, use live help.
