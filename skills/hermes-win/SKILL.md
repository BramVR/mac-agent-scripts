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
- Hermes VM tooling: Docker, Tailscale, `tmux`, Hermes Agent installed; Hermes setup/model config not run.

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

Check:

```bash
ssh hermes-win 'powershell -NoProfile -Command "Get-Service Tailscale,sshd | Select Name,Status,StartType"'
```

## Safety

- Verify host identity before major changes: `hostname` should be `DESKTOP-8FH3QL8`.
- Do not assume stale LAN IPs; prefer Tailscale.
- Do not print secrets from Windows or VM files.
- Keep Home Assistant untouched unless the task is explicitly about HA.
