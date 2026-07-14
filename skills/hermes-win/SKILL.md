---
name: hermes-win
description: "Bram's Windows VirtualBox host for Home Assistant and Hermes agents; Tailscale, SSH, VBoxManage."
---

# Hermes Windows Host

Use when the user says `hermes-win`, `Hermes`, Windows laptop, VirtualBox host, Home Assistant VM, or asks to manage the agent VM host.

## Topology

- Windows host: `DESKTOP-8FH3QL8`
- SSH alias: `hermes-win`
- Tailscale: `hermes-win`
- User: `bramv`
- LAN fallback: `hermes-win-lan`
- VirtualBox: `C:\Program Files\Oracle\VirtualBox\VBoxManage.exe`
- VMs: `HA` running, `HA NEW` unused, `Hermes` running.
- Hermes VM: Ubuntu 24.04, SSH/Tailscale alias `hermes-vm`, user `bram`.
- Hermes VM tooling: Docker, Tailscale, `tmux`, Node 22 via `n`, Hermes Agent installed.
- Hermes Agent: OpenAI Codex OAuth configured, default model `gpt-5.5`, Discord gateway configured, dashboard on VM localhost `127.0.0.1:9119`.
- Windows scheduled task: `Start Hermes VM` starts `Hermes` headless at user logon.

Source of truth:

- This skill is the current source of truth for the host.
- No private manager/ops repo is configured for Bram. If broader host inventory/runbooks appear, ask where to store them first.

## SSH

Prefer Tailscale:

```bash
ssh -o RequestTTY=no -o RemoteCommand=none hermes-win 'hostname'
```

Use LAN fallback only if Tailscale is down:

```bash
ssh -o RequestTTY=no -o RemoteCommand=none hermes-win-lan 'hostname'
```

SSH to Hermes VM:

```bash
ssh hermes-vm 'hostname && hermes --version'
```

Dashboard from Bram's Mac:

```bash
~/Projects/agent-scripts/scripts/hermes-dashboard
```

Manual fallback:

```bash
tmux new-session -d -s hermes-dashboard-tunnel 'ssh -N -L 127.0.0.1:9119:127.0.0.1:9119 hermes-vm'
open http://localhost:9119
```

## VirtualBox

List VMs:

```bash
ssh hermes-win '"C:\Program Files\Oracle\VirtualBox\VBoxManage.exe" list vms'
ssh hermes-win '"C:\Program Files\Oracle\VirtualBox\VBoxManage.exe" list runningvms'
```

Check Hermes VM from host:

```bash
ssh hermes-win '"C:\Program Files\Oracle\VirtualBox\VBoxManage.exe" showvminfo Hermes --machinereadable'
```

Do not stop, clone, delete, or reconfigure `HA` unless explicitly asked.

## Health

Expected host services:

- `Tailscale`: running, auto-start.
- `sshd`: running, auto-start.

Expected Hermes VM services:

- `ssh`: running, auto-start.
- `docker`: running, auto-start.
- `tailscaled`: running, auto-start.
- `hermes-gateway`: running as `bram` user systemd service; linger enabled.
- `hermes-dashboard`: running in VM tmux session, bound to `127.0.0.1:9119`.

Check:

```bash
ssh hermes-win 'powershell -NoProfile -Command "Get-Service Tailscale,sshd | Select Name,Status,StartType"'
ssh hermes-win 'powershell -NoProfile -Command "Get-ScheduledTask -TaskName \"Start Hermes VM\""'
ssh hermes-vm 'hermes status --all && hermes gateway status --deep --full'
ssh hermes-vm 'tmux ls 2>/dev/null || true; ss -ltnp | grep 9119 || true'
```

## Hermes Agent

Default access:

- Dashboard: Mac SSH tunnel to VM localhost; never expose dashboard with `--host 0.0.0.0 --insecure`.
- Discord: private Bram Hermes bot, allowed user only; server channels require `@Bram Hermes`, created threads accept normal replies.
- Model: `openai-codex` provider, `gpt-5.5`.
- Identity: `~/.hermes/SOUL.md`; memory: `~/.hermes/memories/`.

Common commands:

```bash
ssh hermes-vm 'hermes -z "Reply exactly: OK" --provider openai-codex --model gpt-5.5'
ssh hermes-vm 'hermes gateway restart && hermes gateway status --deep --full'
ssh hermes-vm 'curl -fsS http://127.0.0.1:9119/api/status | head -c 500'
```

## GoHealth CLI

- `gohealthcli` is installed on Hermes VM at `~/.local/bin/gohealthcli`; `hermes-gateway` PATH includes it.
- VM config: `~/.config/gohealthcli/config.toml`.
- VM archive: `~/.local/share/gohealthcli/gohealthcli.sqlite` plus `.attachments/`.
- VM secrets: `~/.config/gohealthcli/tokens.json` and OAuth client JSON; owner-only, never print.
- Build source used on 2026-06-28: `BramVR/gohealthcli` `origin/main` schema 24, commit `9f807009cbcf6044d4b4e5c07b47c1c09ea2118d`.
- Daily Discord script: `~/.hermes/scripts/gohealth_daily.sh`; syncs steps from newest archived timestamp minus 30 minutes to now, avoiding whole-day replays after the archive is warm.

Verify:

```bash
ssh hermes-vm '$HOME/.local/bin/gohealthcli doctor --plain'
ssh hermes-vm '$HOME/.local/bin/gohealthcli doctor --online --plain'
ssh hermes-vm '$HOME/.local/bin/gohealthcli status --plain | sed -n "1,12p"'
```

Auth behavior:

- Normal access-token expiry should auto-refresh.
- Broken/revoked refresh auth reports `connection_unhealthy` with `token_status: refresh_failed` or `token_missing`; sync should not open a browser from Discord/cron.
- Reauth is explicit: run `gohealthcli connect --plain`, then `doctor --online --plain`.
- Headless VM reauth may need SSH tunnel/browser handling; fallback is reauth on Mac and copy refreshed `tokens.json` to VM without printing it.
- HTTP 400 is not always auth. On 2026-06-28, failed runs 269/271 used an invalid range (`from` 2026-06-29 after `to` 2026-06-28T16:24Z); bounded run 270 completed.

Reauth check:

```bash
ssh hermes-vm '$HOME/.local/bin/gohealthcli doctor --online --plain'
ssh hermes-vm '$HOME/.local/bin/gohealthcli connect --plain'
ssh hermes-vm '$HOME/.local/bin/gohealthcli doctor --online --plain'
```

Refresh the VM archive from Mac only when no Mac sync is active. Snapshot the database and its attachment sidecar into owner-only temporary storage, stage both remotely, stop VM writers, validate, then rename the pair into place. The timestamped remote backup is the rollback source:

```bash
set -euo pipefail
umask 077
archive=$HOME/.local/share/gohealthcli/gohealthcli.sqlite
snapshot_dir=$(mktemp -d "${TMPDIR:-/tmp}/gohealthcli.XXXXXX")
remote_stage=$(ssh hermes-vm 'umask 077; mktemp -d "$HOME/.local/share/gohealthcli/.restore.XXXXXX"')
cleanup() {
  rm -rf -- "$snapshot_dir"
  ssh hermes-vm rm -rf -- "$remote_stage"
}
trap cleanup EXIT

sqlite3 -cmd '.timeout 30000' "$archive" ".backup '$snapshot_dir/gohealthcli.sqlite'"
chmod 600 "$snapshot_dir/gohealthcli.sqlite"
cp -a "$archive.attachments" "$snapshot_dir/gohealthcli.sqlite.attachments"
find "$snapshot_dir/gohealthcli.sqlite.attachments" -type d -exec chmod 700 {} +
find "$snapshot_dir/gohealthcli.sqlite.attachments" -type f -exec chmod 600 {} +
scp -pr "$snapshot_dir/." "hermes-vm:$remote_stage/"

ssh hermes-vm sh -s -- "$remote_stage" <<'REMOTE'
set -eu
stage=$1
archive=$HOME/.local/share/gohealthcli/gohealthcli.sqlite
attachments=$archive.attachments
backup=$HOME/.local/share/gohealthcli/backup-$(date -u +%Y%m%dT%H%M%SZ)

installed=0
archive_backed_up=0
attachments_backed_up=0
attachments_installed=0
gateway_restart_needed=0
finish() {
  result=$?
  trap - EXIT
  set +e
  if [ "$gateway_restart_needed" -eq 1 ]; then hermes gateway stop >/dev/null 2>&1; fi
  if [ "$installed" -ne 1 ]; then
    if [ "$archive_backed_up" -eq 1 ]; then
      if [ -f "$archive" ]; then mv "$archive" "$stage/failed-gohealthcli.sqlite"; fi
      mv "$backup/gohealthcli.sqlite" "$archive"
    fi
    if [ "$attachments_installed" -eq 1 ]; then
      mv "$attachments" "$stage/failed-gohealthcli.sqlite.attachments"
    fi
    if [ "$attachments_backed_up" -eq 1 ]; then
      mv "$backup/gohealthcli.sqlite.attachments" "$attachments"
    fi
  fi
  if [ "$gateway_restart_needed" -eq 1 ]; then hermes gateway start; fi
  exit "$result"
}
trap finish EXIT
test "$(sqlite3 "$stage/gohealthcli.sqlite" 'PRAGMA quick_check;')" = ok
chmod 600 "$stage/gohealthcli.sqlite"
find "$stage/gohealthcli.sqlite.attachments" -type d -exec chmod 700 {} +
find "$stage/gohealthcli.sqlite.attachments" -type f -exec chmod 600 {} +
gateway_restart_needed=1
hermes gateway stop
mkdir -m 700 "$backup"
mv "$archive" "$backup/"
archive_backed_up=1
if [ -d "$attachments" ]; then
  mv "$attachments" "$backup/"
  attachments_backed_up=1
fi
mv "$stage/gohealthcli.sqlite" "$archive"
mv "$stage/gohealthcli.sqlite.attachments" "$attachments"
attachments_installed=1
doctor_json=$($HOME/.local/bin/gohealthcli doctor --json)
printf '%s' "$doctor_json" | python3 -c 'import json, sys
a = json.load(sys.stdin).get("attachments")
if not isinstance(a, dict):
    raise SystemExit("doctor did not report attachment integrity")
if a.get("orphan_files") or a.get("orphan_rows"):
    raise SystemExit("restored archive has attachment orphans")'
hermes gateway start
installed=1
gateway_restart_needed=0
trap - EXIT
REMOTE
```

## Backups

- Hermes VM offsite backup scaffold: `~/.local/bin/hermes-offsite-backup`.
- Interactive Google Drive/rclone setup helper: `~/.local/bin/hermes-rclone-drive-setup`.
- Config: `~/.config/hermes-offsite-backup.env`.
- User timer installed but disabled until Drive auth/destination configured: `hermes-offsite-backup.timer`.
- Backup bundle includes `hermes backup` zip plus restore notes, user systemd unit, shell dotfiles, and `authorized_keys`.
- Destination should be encrypted: use an `rclone crypt` remote or set `HERMES_BACKUP_ALLOW_PLAINTEXT=1` intentionally.

Check:

```bash
ssh hermes-vm 'bash -n ~/.local/bin/hermes-offsite-backup && systemctl --user list-unit-files "hermes-offsite-backup.*" --no-pager'
```

## Safety

- Verify host identity before major changes: `hostname` should be `DESKTOP-8FH3QL8`.
- Do not assume stale LAN IPs; prefer Tailscale.
- Do not print secrets from Windows or VM files.
- Keep Home Assistant untouched unless the task is explicitly about HA.
