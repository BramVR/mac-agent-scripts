#!/usr/bin/env bash
# Human-in-the-loop reproduction loop.
# Copy this file, edit the steps below, and run it.
# The user runs the script in their terminal and returns the Captured block to
# the agent. Do not run it inside an agent-owned process session.
#
# Usage:
#   bash hitl-loop.template.sh
#
# Two helpers:
#   step "<instruction>"          → show instruction, wait for Enter
#   capture VAR "<question>"      → show question, read lines until terminator
#
# At the end, captured values are printed as KEY=VALUE for the agent to parse.
#
# `capture` prints its value back to the terminal, where the agent reads it — so
# capture observations, and leave signing in to the user as a `step`.

set -euo pipefail

step() {
  printf '\n>>> %s\n' "$1"
  read -r -p "    [Enter when done] " _
}

capture() {
  local var="$1" question="$2" answer="" line
  printf '\n>>> %s\n' "$question"
  printf '    Enter one or more lines, then type __END_CAPTURE__ on its own line.\n'
  while IFS= read -r line; do
    [[ "$line" == "__END_CAPTURE__" ]] && break
    [[ -z "$answer" ]] || answer+=$'\n'
    answer+="$line"
  done
  printf -v "$var" '%s' "$answer"
}

# --- edit below ---------------------------------------------------------

step "Open the app at http://localhost:3000 and sign in."

capture ERRORED "Click the 'Export' button. Did it throw an error? (y/n)"

capture ERROR_MSG "Paste the error message (or 'none'):"

# --- edit above ---------------------------------------------------------

printf '\n--- Captured ---\n'
printf 'ERRORED=%q\n' "$ERRORED"
printf 'ERROR_MSG=%q\n' "$ERROR_MSG"
