# AGENTS.MD

Work style: telegraph; noun-phrases ok; drop grammar; min tokens.

## Agent Protocol
- Contact: Bram (GitHub: `BramVR`, email: `bram.van.rompuy@gmail.com`).
- Workspace: `~/Projects`. Missing Bram repo: clone `https://github.com/BramVR/<repo>.git`.
- 3rd-party/OSS (non-BramVR): clone under `~/Projects/oss`.
- Private ops repo: none configured. If domain/DNS/runbook work appears, ask Bram where to store it before creating a new repo.
- Remote machines: none configured. Do not assume MacBook/Mac Studio SSH targets.
- Files: repo or `~/Projects/agent-scripts`.
- PRs: use `gh pr view/diff` (no URLs).
- “Make a note” => edit AGENTS.md (shortcut; not a blocker). Ignore `CLAUDE.md`.
- Need upstream file: stage in `/tmp/`, then cherry-pick; never overwrite tracked.
- Bugs: add regression test when it fits.
- Keep files <~500 LOC; split/refactor as needed.
- Commits: Conventional Commits (`feat|fix|refactor|build|ci|chore|docs|style|perf|test`).
- Subagents: read `docs/subagent.md`.
- Editor: `code <path>`.
- CI: `gh run list/view` (rerun/fix til green).
- Prefer end-to-end verify; if blocked, say what’s missing.
- New deps: quick health check (recent releases/commits, adoption).
- Slash cmds: `~/.codex/prompts/`.

## Screenshots (“use a screenshot”)
- Pick newest PNG in `~/Desktop` or `~/Downloads`.
- Verify it’s the right UI (ignore filename).
- Size: `sips -g pixelWidth -g pixelHeight <file>` (prefer 2×).
- Optimize: `imageoptim <file>` (install: `brew install imageoptim-cli`).
- Replace asset; keep dimensions; commit; run gate; verify CI.

## Important Locations
- Blog repo: none configured.
- Notes/Runbooks: none configured.
- OpenAI/Codex limits tracking: none configured.
- Codex debugging: read local source first: `~/Projects/codex`; start `codex-rs/AGENTS.md`, then targeted `rg` in `codex-rs/{core,tui,exec,cli,app-server,app-server-protocol,config}`.
- Obsidian/notes vault: none configured.
- Sparkle keys: none configured.

## Data Sources
- Local message/archive tools are not configured by default on Bram's machine.
- Do not assume `discrawl`, `slacrawl`, `whatsapp`/`wacrawl`/`wacli`, `notcrawl`, `imsg`, `beeper`, `birdclaw`, or `xurl` exist. Check the repo/tool first, and ask Bram before setting up new local archives or sending messages.
- `gog`: Google services CLI at `/opt/homebrew/bin/gog`, source at `~/Projects/gogcli`; auth not configured until Bram provides a Google Desktop OAuth client JSON and completes browser consent.
- For message/history questions, prefer explicitly configured local archives over web/API when available; state freshness + gaps.
- Env/API keys: check `~/.profile`; secrets/tokens via `op` only inside tmux, and only when strictly needed. Never call `op` directly.

## Docs
- Start: run docs list (`docs:list` script, or repo-local `bin/docs-list` if present). If the repo has neither and `~/Projects/agent-scripts/bin/docs-list` exists, run that shared helper as a fallback and treat its output as an inventory, not proof the repo has its own helper. Ignore if no helper is installed.
- Follow links until domain makes sense; honor `Read when` hints.
- Keep notes short; update docs when behavior/API changes (no ship w/o docs).
- Add `read_when` hints on cross-cutting docs.

## PR Feedback
- Replies: cite fix + file/line; resolve threads only after fix lands.
- When merging a PR: thank the contributor in `CHANGELOG.md`.
- User-facing fixes/landed PRs: changelog unless pure test/internal.

## Flow & Runtime
- Use repo’s package manager/runtime; no swaps w/o approval.
- Use Codex background for long jobs; tmux only for interactive/persistent (debugger/server).
- zsh: don't use `status` as a variable.
- Passwords/secrets: check `~/.profile` first. `op`/1Password CLI is last resort, must always run inside `tmux`, never directly.
- NEVER run `op` directly in a normal shell. No exceptions. This includes harmless-looking diagnostics: no direct `op --version`, `op account list`, `op whoami`, `op vault list`, `op item list`, `op read`, or `op item get`.
- `tmux` is necessary for `op`, but not sufficient: do not spam 1Password. No parallel `op`; no repeated probe sessions; no broad vault/item enumeration; no trial-and-error secret discovery.
- Before any `op` call, state the exact single item/field/secret needed and why. If more than one 1Password command seems necessary, stop and ask Bram before continuing.
- Every command whose executable is `op` must run inside one named `tmux` session. The whole pipeline must be inside that `tmux` command: pipes, redirects, command substitution, OTP reads, and publish commands that call `op`.
- Do not probe `op` outside `tmux` to check whether it works. If `tmux` cannot be used, stop and say so.
- `op` recipe: one deliberate `tmux` command; targeted item/field only; avoid temp files unless needed; delete temp files after; inspect only non-secret metadata; keep secret output redacted; kill the tmux session when done.
- 1Password account: `my.1password.com`. Service account: none configured. If automation needs one, ask Bram for the env var name, vault name, and exact item/field; do not invent or enumerate.
- Remote secret files: stream without printing. If `gh secret set` from stdin stores empty, retry with `--body` from an in-memory shell var after non-secret shape/size checks; verify via workflow evidence that the secret is present.
- OpenClaw: not configured. Do not assume OpenClaw, Molty, Clownfish, or Clawsweeper workflows.

## Build / Test
- Before handoff: run full gate (lint/typecheck/tests/docs).
- CI red: `gh run list/view`, rerun, fix, push, repeat til green.
- Release: read `docs/RELEASING.md` (or find best checklist if missing).

## Git
- Safe by default: `git status/diff/log`. Push only when user asks.
- End in visible checkout/branch user expects; avoid surprise temp worktrees.
- Branch changes require user consent.
- Destructive ops forbidden unless explicit (`reset --hard`, `clean`, `restore`, `rm`, …).
- Remotes under `~/Projects`: prefer HTTPS; flip SSH->HTTPS before pull/push.
- Commit helper on PATH: `committer` (bash). Prefer it; if repo has `./scripts/committer`, use that.
- Don’t delete/rename unexpected stuff; stop + ask.
- No repo-wide S/R scripts; keep edits small/reviewable.
- If user types a command (“pull and push”), that’s consent for that command.
- No amend unless asked.
- Unrecognized changes: assume other agent; keep going; focus your changes. If it causes issues, stop + ask user.

## Tools

Read `~/Projects/agent-scripts/tools.md` for the full tool catalog if it exists.

### peekaboo
- Screen tools: `~/Projects/Peekaboo`. Cmds: `capture`, `see`, `click`, `list`, `tools`, `permissions status`.
- Needs Screen Recording + Accessibility. Docs: `~/Projects/Peekaboo/docs/commands/`.
- Not configured on Bram's machine; check path before use.

### committer
- Commit helper (PATH). Stages only listed paths; required here. Repo may also ship `./scripts/committer`.

### mcporter / iterm / firecrawl / XcodeBuildMCP
- MCP launcher: `npx mcporter <server>` (see `npx mcporter --help`). Common: `iterm`, `firecrawl`, `XcodeBuildMCP`.

### imsg
- iMessage/SMS CLI. Use `$imsg`. Send only when explicitly asked.
- Not configured on Bram's machine; do not assume it exists.

### gh
- GitHub CLI for PRs/CI/releases. Given issue/PR URL (or `/pull/5`): use `gh`, not web search.

### tmux
- Use only when you need persistence/interaction (debugger/server).
- Quick refs: `tmux new -d -s codex-shell`, `tmux attach -t codex-shell`, `tmux list-sessions`, `tmux kill-session -t codex-shell`.
