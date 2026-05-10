# Agent Scripts

This folder collects Bram's shared agent instructions, local skills, and small
guardrail helpers for reuse across projects.

This repo is a BramVR-maintained fork of the original `steipete/agent-scripts`
setup. Some skills and docs still preserve upstream provenance or optional
Peter/OpenClaw-specific workflows; the active shared defaults live in
`AGENTS.MD`.

Additional skills (copied 2025-12-31) are from @Dimillian’s public `Dimillian/Skills` repository:
- `skills/swift-concurrency-expert`
- `skills/swiftui-liquid-glass`
- `skills/swiftui-performance-audit`
- `skills/swiftui-view-refactor`

## Syncing With Other Repos
- Treat this repo as Bram's canonical shared agent setup.
- When someone says "sync agent scripts," pull the latest changes here, ensure downstream repos have the pointer-style `AGENTS.MD`, copy any helper updates into place, and reconcile differences before moving on.
- Keep shared helper scripts dependency-light and portable. Do not add repo-specific imports to helpers that are meant to be copied into other projects.

## Pointer-Style AGENTS
- Shared guardrail text now lives only inside this repo: `AGENTS.MD` (shared rules + tool list).
- Every consuming repo’s `AGENTS.MD` is reduced to the pointer line `READ ~/Projects/agent-scripts/AGENTS.MD BEFORE ANYTHING (skip if missing).` Place repo-specific rules **after** that line if they’re truly needed.
- Do **not** copy the `[shared]` or `<tools>` blocks into other repos anymore. Instead, keep this repo updated and have downstream workspaces re-read `AGENTS.MD` when starting work.
- When updating the shared instructions, edit `agent-scripts/AGENTS.MD`; global Codex/Claude files consume it through symlinks.

## Global Agent Setup
- Global Codex/Claude instructions can point at this repo:
  - `~/.codex/AGENTS.md -> ~/Projects/agent-scripts/AGENTS.MD`
  - `~/.claude/CLAUDE.md -> ~/Projects/agent-scripts/AGENTS.MD`
  - `~/.claude/AGENTS.md -> ~/Projects/agent-scripts/AGENTS.MD`
- Current global Codex skills are installed individually:
  - `~/.codex/skills/oracle -> ~/Projects/agent-scripts/skills/oracle`
  - `~/.codex/skills/video-transcript-downloader -> ~/Projects/agent-scripts/skills/video-transcript-downloader`
  - `~/.codex/skills/gog -> ~/Projects/gogcli/.agents/skills/gog`
- Keep shared skills as real folders in `skills/`. For repo-owned skills, keep the canonical skill in the owning repo and expose it here with a tracked relative symlink only when that repo exists locally.
- Some optional crawler/messaging symlinks may be absent on Bram's machine; agents must check before use.

## Committer Helper (`scripts/committer`)
- **What it is:** Bash helper that stages exactly the files you list, enforces non-empty commit messages, and creates the commit.

## Skill Validator Hook
- **What it is:** `scripts/validate-skills` checks every discoverable `skills/*/SKILL.md` file for valid YAML front matter and required `name`/`description` fields.
- **Hook:** `hooks/pre-commit` runs the validator before commits. Enable the tracked hooks in a checkout with `git config core.hooksPath hooks`.

## Docs Lister (`scripts/docs-list.ts`)
- **What it is:** tsx script that walks `docs/`, enforces front-matter (`summary`, `read_when`), and prints the summaries surfaced by `pnpm run docs:list`. Other repos can wire the same command into their onboarding flow.
- **Binary build:** `bin/docs-list` is the compiled Bun CLI; regenerate it after editing `scripts/docs-list.ts` via `bun build scripts/docs-list.ts --compile --outfile bin/docs-list`.

## Browser Tools (`bin/browser-tools`)
- **What it is:** A standalone Chrome helper inspired by Mario Zechner’s [“What if you don’t need MCP?”](https://mariozechner.at/posts/2025-11-02-what-if-you-dont-need-mcp/) article. It launches/inspects DevTools-enabled Chrome profiles, pastes prompts, captures screenshots, and kills stray helper processes without needing the full Oracle CLI.
- **Usage:** Prefer the compiled binary: `bin/browser-tools --help`. Common commands include `start --profile`, `nav <url>`, `eval '<js>'`, `screenshot`, `search --content "<query>"`, `content <url>`, `inspect`, and `kill --all --force`.
- **Rebuilding:** The binary is not tracked in git. Re-generate it with `bun build scripts/browser-tools.ts --compile --target bun --outfile bin/browser-tools` (requires Bun) and leave transient `node_modules`/`package.json` out of the repo.
- **Portability:** The tool has zero repo-specific imports. Copy the script or the binary into other automation projects as needed and keep this copy in sync with downstream forks. It detects Chrome sessions launched via `--remote-debugging-port` **and** `--remote-debugging-pipe`, so list/kill works for both styles.

## Sync Expectations
- This repository is Bram's canonical mirror for shared guardrail helpers. Whenever you edit `scripts/committer`, `scripts/docs-list.ts`, or related guardrail files in another repo, copy the changes back here when those helpers should stay shared.
- When someone asks to “sync agent scripts,” update this repo, compare it against the active project, and reconcile differences in both directions before continuing.

## Bram Agent Instructions (pointer workflow)
- The shared guardrails live in `agent-scripts/AGENTS.MD`. Downstream repos should contain the pointer line plus any repo-local additions.
- During a sync sweep: pull latest `agent-scripts`, ensure each target repo's `AGENTS.MD` contains the pointer line at the top, append any repo-local notes beneath it, and update helper scripts as needed.
- If a repo needs custom instructions, clearly separate them from the pointer so future sweeps don’t overwrite local content.
