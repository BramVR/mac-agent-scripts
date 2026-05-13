# Tools Reference

CLI tools available or known to agents. Use only when installed/configured on Bram's machine; check paths before relying on optional tools.

## bird 🐦
Twitter/X CLI for posting, replying, reading tweets.

**Location**: `~/Projects/bird/bird`

**Status**: Not configured on Bram's machine.

**Commands**:
```bash
bird tweet "<text>"                    # Post a tweet
bird reply <tweet-id-or-url> "<text>"  # Reply to a tweet
bird read <tweet-id-or-url>            # Fetch tweet content
bird replies <tweet-id-or-url>         # List replies to a tweet
bird thread <tweet-id-or-url>          # Show full conversation thread
bird search "<query>" [-n count]       # Search tweets
bird mentions [-n count]               # Find tweets mentioning @clawdbot
bird whoami                            # Show logged-in account
bird check                             # Show credential sources
```

**Auth**: Uses Firefox cookies by default. Pass `--firefox-profile <name>` to switch.

---

## sonoscli 🔊
Control Sonos speakers over local network (UPnP/SOAP).

**Location**: `~/Projects/sonoscli/bin/sonos`

**Status**: Not configured on Bram's machine.

**Commands**:
```bash
sonos discover                         # Find speakers on network
sonos status --name "Room"             # Current playback status
sonos play/pause/stop --name "Room"    # Playback control
sonos next/prev --name "Room"          # Track navigation
sonos volume get/set --name "Room" 25  # Volume control
sonos mute get/toggle --name "Room"    # Mute control

# Grouping
sonos group status                     # Show current groups
sonos group join --name "A" --to "B"   # Join A into B's group
sonos group unjoin --name "Room"       # Make standalone
sonos group party --to "Room"          # Join all to one group

# Spotify (via SMAPI)
sonos smapi search --service "Spotify" --category tracks "query"
sonos open --name "Room" spotify:track:<id>
```

**Known issues**:
- SSDP multicast may fail; use `--ip <speaker-ip>` as fallback
- Default HTTP keep-alives can cause timeouts (fix pending: DisableKeepAlives)

---

## peekaboo 👀
Screenshot, screen inspection, and click automation.

**Location**: `/opt/homebrew/bin/peekaboo` (Homebrew: `steipete/tap/peekaboo`)

**Status**: Configured on Bram's machine. Version 3.1.2; Screen Recording + Accessibility granted.

**Commands**:
```bash
peekaboo image                         # Take screenshot
peekaboo see                           # Describe what's on screen (OCR)
peekaboo click                         # Click at coordinates
peekaboo list                          # List windows/apps
peekaboo tools                         # Show available tools
peekaboo permissions status            # Check TCC permissions
```

**Requirements**: Screen Recording + Accessibility permissions.

**Docs**: `https://github.com/openclaw/Peekaboo/tree/main/docs/commands`

---

## sweetistics 📊
Twitter/X analytics desktop app (Tauri).

**Location**: `~/Projects/sweetistics`

**Status**: Not configured on Bram's machine.

Use for deeper Twitter data analysis beyond what `bird` provides.

---

## clawdis 📡
WhatsApp/Telegram messaging gateway and agent interface.

**Location**: `~/Projects/clawdis`

**Status**: Not configured on Bram's machine.

**Commands**:
```bash
clawdis login                          # Link WhatsApp via QR
clawdis send --to <number> --message "text"  # Send message
clawdis agent --message "text"         # Talk to agent directly
clawdis gateway                        # Run WebSocket gateway
clawdis status                         # Session health
```

---

## oracle 🧿
Hand prompts + files to other AIs (GPT-5 Pro, etc.).

**Status**: Configured as a global Codex skill symlink; CLI is fetched via `npx`.

**Usage**: `npx -y @steipete/oracle --help` (run once per session to learn syntax)

---

## gog
Google services CLI for Gmail, Calendar, Drive, Docs, Sheets, Slides, Forms,
Apps Script, Contacts, Tasks, People, and Workspace flows.

**Location**: `~/Projects/gogcli/bin/gog`

**Status**: Installed on PATH at `/opt/homebrew/bin/gog`; auth not configured yet.

**Commands**:
```bash
gog --version
gog auth list --check --json --no-input
gog auth doctor --check --json --no-input
gog schema --json
```

For agents, prefer `--json`, `--no-input`, explicit `--account`, and
`--gmail-no-send` unless sending mail was explicitly requested.

---

## gh
GitHub CLI for PRs, issues, CI, releases.

**Status**: Installed at `/opt/homebrew/bin/gh`.

**Usage**: `gh help`

When someone shares a GitHub URL, use `gh` to read it:
```bash
gh issue view <url> --comments
gh pr view <url> --comments --files
gh run list / gh run view <id>
```

---

## mcporter
MCP server launcher for browser automation, web scraping.

**Status**: Available through `npx` if network/package access is available.

**Usage**: `npx mcporter --help`

Common servers: `iterm`, `firecrawl`, `XcodeBuildMCP`
