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
- Hermes Agent: OpenAI Codex OAuth configured, default model `gpt-5.4`, Discord gateway configured, dashboard on VM localhost `127.0.0.1:9119`.
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
- Model: `openai-codex` provider, `gpt-5.4`.
- Identity: `~/.hermes/SOUL.md`; memory: `~/.hermes/memories/`.

Common commands:

```bash
ssh hermes-vm 'hermes -z "Reply exactly: OK" --provider openai-codex --model gpt-5.4'
ssh hermes-vm 'hermes gateway restart && hermes gateway status --deep --full'
ssh hermes-vm 'curl -fsS http://127.0.0.1:9119/api/status | head -c 500'
```

## Safety

- Verify host identity before major changes: `hostname` should be `DESKTOP-8FH3QL8`.
- Do not assume stale LAN IPs; prefer Tailscale.
- Do not print secrets from Windows or VM files.
- Keep Home Assistant untouched unless the task is explicitly about HA.
