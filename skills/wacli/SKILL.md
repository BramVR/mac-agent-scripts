---
name: wacli
description: "WhatsApp linked-device CLI: auth, sync, search, send, live state."
---

# wacli

Use for WhatsApp linked-device work: pairing, live sync, sending, reactions,
mark-read/archive/pin/mute, groups/channels, media, and account stores.

## Sources

- Repo: `~/Projects/oss/wacli`
- Built CLI: `~/Projects/oss/wacli/dist/wacli`
- Installed CLI: `~/.local/bin/wacli`
- Config: `~/.wacli/config.yaml`
- Default store: `~/.wacli`
- Named stores: `~/.wacli/accounts/<name>`

## Safety

- Prefer `--read-only` or `WACLI_READONLY=1` for inspection.
- Use `--json` for parsing.
- Do not send messages, react, mark read, mutate chats/groups, or sync follow-mode unless explicitly asked.
- Do not write `session.db` directly.
- Keep named accounts isolated.

## Setup Checks

```bash
wacli version --json
wacli doctor --json
wacli accounts list --json
```

Pairing needs Bram to scan a QR or provide a phone-pairing flow:

```bash
wacli accounts add me
# or
wacli auth --qr-format terminal
```

After pairing:

```bash
wacli --account me auth status --read-only --json
wacli --account me sync --once --events
wacli --account me doctor --read-only --json
```

## Read-Only Work

```bash
wacli --account me chats list --read-only --json
wacli --account me messages list --read-only --json --limit 20
wacli --account me messages search --read-only --json "query"
```

## Sending / Mutations

Only after explicit user intent:

```bash
wacli --account me send text --to JID_OR_NAME --message "message"
wacli --account me send file --to JID_OR_NAME --file ./file.jpg --caption "caption"
wacli --account me chats mark-read --chat JID
```
