#!/usr/bin/env bash
set -euo pipefail

repo="/Users/bram/Projects/mac_maya_dev"
config=""
deploy=0
dry_run=0

usage() {
  printf '%s\n' \
    "Usage: launch.sh [--repo PATH] [--config PATH] [--deploy] [--dry-run]" \
    "" \
    "Launch or reconnect to the managed Maya 2024 session." \
    "--deploy runs the configured source gate and selects a new immutable snapshot." \
    "It is refused while a session is already running."
}

while (($#)); do
  case "$1" in
    --repo)
      repo=${2:?missing value for --repo}
      shift 2
      ;;
    --config)
      config=${2:?missing value for --config}
      shift 2
      ;;
    --deploy)
      deploy=1
      shift
      ;;
    --dry-run)
      dry_run=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      printf 'error: unknown argument: %s\n' "$1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ -z "$config" ]]; then
  config="$repo/.maya-dev.toml"
fi

[[ -d "$repo" ]] || { printf 'error: repo missing: %s\n' "$repo" >&2; exit 1; }
[[ -f "$config" ]] || { printf 'error: config missing: %s\n' "$config" >&2; exit 1; }

python3 - "$config" <<'PY'
from pathlib import Path
import sys
import tomllib

path = Path(sys.argv[1])
with path.open("rb") as handle:
    data = tomllib.load(handle)
remote = data.get("remote", {})
sessiond = data.get("sessiond", {})
errors = []
if remote.get("ssh_host") != "maya-win":
    errors.append("remote.ssh_host must be maya-win")
if remote.get("port") != 7002:
    errors.append("remote.port must be 7002")
if "Maya2024" not in str(sessiond.get("maya_exe", "")):
    errors.append("sessiond.maya_exe must target Maya2024")
if sessiond.get("interactive_task") != "MayaDevSessiond2024":
    errors.append("sessiond.interactive_task must be MayaDevSessiond2024")
if errors:
    raise SystemExit("unsafe config: " + "; ".join(errors))
print(f"config: {path}")
print("target: maya-win / Maya 2024 / 127.0.0.1:7002 / MayaDevSessiond2024")
PY

base=(uv run maya-dev --config "$config")

show_command() {
  printf 'would run:'
  printf ' %q' "$@"
  printf '\n'
}

run() {
  if ((dry_run)); then
    show_command "$@"
    return 0
  fi
  printf 'run:'
  printf ' %q' "$@"
  printf '\n'
  "$@"
}

status_json() {
  local output rc
  set +e
  output=$("${base[@]}" --json status 2>/dev/null)
  rc=$?
  set -e
  if [[ -z "$output" ]]; then
    printf '{"derived_status":"unknown","status_exit":%d}\n' "$rc"
  else
    printf '%s\n' "$output"
  fi
}

status_name() {
  python3 -c 'import json,sys; print(json.load(sys.stdin).get("derived_status", "unknown"))'
}

poll_running() {
  local attempts=${1:-6}
  local state payload
  for ((i=1; i<=attempts; i++)); do
    payload=$(status_json)
    state=$(printf '%s' "$payload" | status_name)
    printf 'status: %s\n' "$state"
    if [[ "$state" == "running" ]]; then
      return 0
    fi
    if [[ "$state" != "starting" && "$state" != "unknown" ]]; then
      return 1
    fi
    sleep 10
  done
  return 1
}

cd "$repo"
run "${base[@]}" --json windows check

if ((dry_run)); then
  show_command "${base[@]}" --json status
  if ((deploy)); then
    show_command "${base[@]}" check
    show_command "${base[@]}" deploy
  fi
  show_command "${base[@]}" start
  show_command "${base[@]}" call scene.info
  show_command "${base[@]}" status
  show_command "${base[@]}" doctor
  exit 0
fi

payload=$(status_json)
state=$(printf '%s' "$payload" | status_name)
printf 'status: %s\n' "$state"

if [[ "$state" == "running" ]]; then
  if ((deploy)); then
    printf '%s\n' "error: refusing --deploy while Maya is running; preserve the active session" >&2
    exit 1
  fi
elif [[ "$state" == "starting" ]]; then
  printf '%s\n' "Maya is already starting; waiting instead of issuing another start."
  poll_running 6 || { printf '%s\n' "error: session did not reach running" >&2; exit 1; }
else
  if ((deploy)); then
    run "${base[@]}" check
    run "${base[@]}" deploy
  fi
  set +e
  run "${base[@]}" start
  start_rc=$?
  set -e
  if ((start_rc != 0)); then
    printf '%s\n' "start returned nonzero; checking for the known late-readiness race before retrying"
  fi
  poll_running 6 || { printf '%s\n' "error: managed session is not running; inspect status/logs, do not repeat start blindly" >&2; exit 1; }
fi

run "${base[@]}" call scene.info
run "${base[@]}" status
run "${base[@]}" doctor
printf '%s\n' "ready: use '${base[*]} call --list' to inventory MayaMCP tools"
