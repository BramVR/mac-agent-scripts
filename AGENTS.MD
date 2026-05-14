Work style: telegraph; noun-phrases ok; drop grammar; min tokens.
Codex CLI output: avoid Markdown tables by default; they render poorly there. Use short bullets or `key: value` lines instead. Only use a table when explicitly requested.

## Core

- Contact: Bram (GitHub: `BramVR`, email: `bram.van.rompuy@gmail.com`).
- Workspace: `~/Projects`. Missing Bram repo: clone `https://github.com/BramVR/<repo>.git`.
- 3rd-party/OSS (non-BramVR): clone under `~/Projects/oss`.
- Private ops repo: none configured. If domain/DNS/runbook work appears, ask Bram where to store it before creating a new repo.
- Remote hosts: `hermes-win`, `hermes-vm`; see `skills/hermes-win/SKILL.md`.
- Files: repo or `~/Projects/agent-scripts`.
- "Make a note" here => terse `AGENTS.MD` edit. Ignore `CLAUDE.md`.
- `ship` => changelog, commit in groups, push, pull.
- Release closeout: after verified release, bump changelog to next patch `Unreleased`, commit.
- Release verify: confirm release docs/notes contain changelog; if missing/stale, fix before closeout.
- npm release verify: `npm view <pkg>@<version>` shows version, dist-tag, tarball, integrity, publish time; GitHub tag + Release exist; Release body links npm version page, registry tarball, integrity, CI/proof.
- Changelogs: match file style; prefer one bullet per entry on one line. Do not hard-wrap changelog bullets just because prose is long.
- Skills are canonical for tool workflows. Keep this file to hard rules only.
- Editing here/skills: token-efficient, relaxed grammar, terse descriptions.
- Skill descriptions: short generic trigger phrase, not summary; no personal names, long paths, or workflow narration unless needed for routing.
- Skill frontmatter: quote `description`; after SKILL.md edits, YAML-parse frontmatter before commit.
- Read `~/Projects/agent-scripts/tools.md` when the tool catalog matters.

## Routing

- Screenshots/assets: newest PNG in `~/Desktop` or `~/Downloads`; verify UI before replacing.
- Private/history: local archives first; verify freshness for current questions.
- Secrets: check `~/.profile` anytime you need an API key or for e2e testing; `$one-password` for op/1Password.
- Codex debugging: read local source first: `~/Projects/codex`; start `codex-rs/AGENTS.md`, then targeted `rg` in `codex-rs/{core,tui,exec,cli,app-server,app-server-protocol,config}`.
- Blog repo, notes/runbooks, OpenAI/Codex limits tracking, Sparkle keys: none configured.

## Project Defaults

- Need upstream file: stage in `/tmp/`, then cherry-pick; never overwrite tracked files.
- Bugs: add regression test when it fits.
- Use repo package manager/runtime; no swaps without approval.
- Docs: read repo docs before coding; update docs/changelog for user-visible behavior changes.
- Inline code comments: brief notes for tricky, bug-prone, or previously buggy logic.
- New deps: quick health check for recent releases/commits/adoption.
- Start docs work: run docs list (`docs:list`, repo-local `bin/docs-list`, or shared `~/Projects/agent-scripts/bin/docs-list` as inventory only).
- Follow docs links until domain makes sense; honor `Read when` hints.
- Keep notes short; add `read_when` hints on cross-cutting docs.

## PR / CI

- GitHub broad reads: prefer shimmed `gh` / `gitcrawl gh` first. Raw `gh api search/* -f ...` needs `--method GET`; gitcrawl shim sanitizes this.
- PR refs: use `gh pr view/diff`, not web search.
- PRs: prefer rewriting/fixing the PR, then merging it, over closing and committing equivalent files directly.
- Landing own draft PR after explicit land request: ignore draft status; mark ready if needed and continue.
- `fix ci`: consent to pull, commit, push; fix/rerun/watch until CI green.
- CI: `gh run list/view`; rerun/fix until green when asked.
- `rewrite commits + land`: clean stack, agreed focused proof only, force-push, merge. No Codex review, PR-body proof polish, or CI babysitting unless asked.
- Replies: cite fix + file/line; resolve threads only after fix lands.
- Issue fixed on `main` with proof: comment proof + commit/PR, then close.
- User-facing fixes/landed PRs: changelog unless pure test/internal.
- Contributor PR authors should not edit changelog; maintainer/AI adds entry at merge.
- After landing: final includes 2-5 sentence recap of what landed.
- After landing: checkout `main`, pull `--ff-only`, verify `git status -sb`, then final.
- When merging contributor PRs: thank contributor in `CHANGELOG.md`.
- Unpushable contributor PRs (`maintainerCanModify=false`/no head write): if fixups needed, recreate locally from PR head/diff, make one maintainer commit, push it, then close PR with comment.
- Preserve contributor credit: commit body includes `Co-authored-by: Name <email>` from PR commit author; changelog still thanks `@login` when user-facing.
- PR fixups from repo cwd: use that checkout. No worktrees unless asked; if awkward, ask.
- Close comment: link landed commit, explain PR branch could not be updated, thank author, suggest enabling "Allow edits by maintainers" for future PRs.

## Runtime Safety

- zsh: don't use `status` as a variable.
- Passwords/secrets: check `~/.profile` first. `op`/1Password CLI is last resort, must always run inside `tmux`, never directly.
- NEVER run `op` directly in a normal shell. No exceptions. This includes harmless-looking diagnostics: no direct `op --version`, `op account list`, `op whoami`, `op vault list`, `op item list`, `op read`, or `op item get`.
- `tmux` is necessary for `op`, but not sufficient: do not spam 1Password. No parallel `op`; no repeated probe sessions; no broad vault/item enumeration; no trial-and-error secret discovery.
- Before any `op` call, state the exact single item/field/secret needed and why. If more than one 1Password command seems necessary, stop and ask Bram before continuing.
- Every command whose executable is `op` must run inside one named `tmux` session. The whole pipeline must be inside that `tmux` command: pipes, redirects, command substitution, OTP reads, and publish commands that call `op`.
- Do not probe `op` outside `tmux` to check whether it works. If `tmux` cannot be used, stop and say so.
- `op` recipe: one deliberate `tmux` command; targeted item/field only; avoid temp files unless needed; delete temp files after; inspect only non-secret metadata; keep secret output redacted; kill the tmux session when done.
- 1Password account: `my.1password.com`. Service account: none configured. If automation needs one, ask Bram for the env var name, vault name, and exact item/field; do not invent or enumerate.
- Secrets: never run `env`, `set`, `export -p`, or broad secret regex dumps in a normal shell. Query exact names only; redact values.
- Remote secret files: stream without printing. If `gh secret set` from stdin stores empty, retry with `--body` from an in-memory shell var after non-secret shape/size checks; verify via workflow evidence that the secret is present.
- Public GitHub bodies: never inline double-quoted text with backticks, `$`, shell snippets, env names, or user text. Use temp file + `cat <<'EOF'` + inspect + `--body-file`.
- After touching secrets/env, public `gh` writes use token env unset where possible: `env -u GITHUB_TOKEN -u GH_TOKEN -u HOMEBREW_GITHUB_API_TOKEN ...`.
- OpenClaw: not configured. Do not assume OpenClaw, Molty, Clownfish, Clawsweeper, or ClickClack workflows.

## Data Sources

- Local message/archive tools are not configured by default on Bram's machine.
- Do not assume `discrawl`, `slacrawl`, `whatsapp`/`wacrawl`/`wacli`, `notcrawl`, `imsg`, `beeper`, `birdclaw`, or `xurl` exist. Check the repo/tool first, and ask Bram before setting up new local archives or sending messages.
- `gog`: Google services CLI at `/opt/homebrew/bin/gog`, source at `~/Projects/gogcli`; auth not configured until Bram provides a Google Desktop OAuth client JSON and completes browser consent.
- For message/history questions, prefer explicitly configured local archives over web/API when available; state freshness + gaps.

## Build / Test

- Before handoff: run full gate (lint/typecheck/tests/docs).
- CI red: `gh run list/view`, rerun, fix, push, repeat til green.
- Release: read `docs/RELEASING.md` or find best checklist if missing.

## Git

- If cwd is in a git repo: work there. Do not jump to sibling checkout unless asked.
- No `git worktree` from CLI sessions unless user asks. If dirty/wrong branch/awkward: ask.
- Branch switch/checkout ok when task needs it and repo rules allow.
- `~/Projects` has many intentional same-repo checkouts. Treat as user-managed, not scratch.
- If cwd is not a git repo: freeform; pick sensible folder, say path before edits. Worktrees ok if useful.
- Safe by default: `git status/diff/log`.
- Push only when user asks.
- End in visible checkout/branch user expects.
- Branch changes require user consent.
- Destructive ops forbidden unless explicit: `reset --hard`, `clean`, `restore`, `rm`, etc.
- Remotes under `~/Projects`: prefer HTTPS; flip SSH->HTTPS before pull/push.
- Commit helper on PATH: `committer` (bash). Prefer it; if repo has `./scripts/committer`, use that.
- Commits: Conventional Commits (`feat|fix|refactor|build|ci|chore|docs|style|perf|test`).
- No repo-wide S/R scripts; keep edits small/reviewable.
- If user types a command ("pull and push"), that's consent for that command.
- No amend unless asked.
- Unrecognized changes: assume other agent; keep going; focus your changes. If it causes issues, stop + ask user.

## Tools

- Full catalog: `~/Projects/agent-scripts/tools.md` if present.
- `peekaboo`: screen tools at `~/Projects/Peekaboo`; check path/permissions first, not configured by default.
- `committer`: stage only listed paths; required here.
- `mcporter`: `npx mcporter <server>`; common: `iterm`, `firecrawl`, `XcodeBuildMCP`.
- `imsg`: send only when explicitly asked; not configured by default.
- `gh`: PRs/CI/releases; given issue/PR URL or `/pull/5`, use `gh`.
- `tmux`: use only for persistence/interaction; quick refs: `tmux new -d -s codex-shell`, `tmux attach -t codex-shell`, `tmux list-sessions`, `tmux kill-session -t codex-shell`.
