# Agent Scripts

This folder collects Bram's shared agent instructions, local skills, and small guardrail helpers for reuse across projects.

This repo is a BramVR-maintained fork of the original `steipete/agent-scripts` setup. Active shared defaults live in `AGENTS.MD`.

Canonical contents:
- `AGENTS.MD`: shared hard rules for Codex/Claude-style agents
- `skills/`: reusable workflow skills, including repo-owned skills exposed by symlink
- `scripts/`: dependency-light helpers used across projects
- `hooks/`: local guardrails such as skill validation

## Skills

Skills are the main routing layer. Each `skills/<name>/SKILL.md` has YAML front matter:

```yaml
---
name: skill-name
description: "Short generic trigger phrase."
---
```

Rules:
- Keep descriptions short and generic; optimize for routing, not documentation.
- Keep skill bodies terse and operational.
- Prefer helper scripts under `skills/<name>/scripts/` when a workflow has repeatable commands.
- Validate after edits: `scripts/validate-skills`.
- Quote `description` in front matter.

Global Codex skills are installed individually:
- `~/.codex/skills/oracle -> ~/Projects/agent-scripts/skills/oracle`
- `~/.codex/skills/wacrawl -> ~/Projects/oss/wacrawl/.agents/skills/wacrawl`
- `~/.codex/skills/codex-debugging -> ~/Projects/agent-scripts/skills/codex-debugging`
- `~/.codex/skills/github-deep-review -> ~/Projects/agent-scripts/skills/github-deep-review`
- `~/.codex/skills/github-author-context -> ~/Projects/agent-scripts/skills/github-author-context`
- `~/.codex/skills/github-cache-hygiene -> ~/Projects/agent-scripts/skills/github-cache-hygiene`
- `~/.codex/skills/github-project-triage -> ~/Projects/agent-scripts/skills/github-project-triage`
- `~/.codex/skills/gog -> ~/Projects/gogcli/.agents/skills/gog`
- `~/.codex/skills/hermes-win -> ~/Projects/agent-scripts/skills/hermes-win`
- `~/.codex/skills/browser-use -> ~/Projects/agent-scripts/skills/browser-use`
- `~/.codex/skills/to-issues -> ~/Projects/agent-scripts/skills/to-issues`
- `~/.codex/skills/grill-with-docs -> ~/Projects/agent-scripts/skills/grill-with-docs`
- `~/.codex/skills/one-password -> ~/Projects/agent-scripts/skills/one-password`
- `~/.codex/skills/obsidian -> ~/Projects/agent-scripts/skills/obsidian`
- `~/.codex/skills/peekaboo -> ~/Projects/agent-scripts/skills/peekaboo`
- `~/.codex/skills/npm -> ~/Projects/agent-scripts/skills/npm`
- `~/.codex/skills/tdd -> ~/Projects/agent-scripts/skills/tdd`
- `~/.codex/skills/to-prd -> ~/Projects/agent-scripts/skills/to-prd`
- `~/.codex/skills/bram-maintainer-loop -> ~/Projects/agent-scripts/skills/bram-maintainer-loop`
- `~/.codex/skills/autoreview -> ~/Projects/agent-scripts/skills/autoreview`
- `~/.codex/skills/video-transcript-downloader -> ~/Projects/agent-scripts/skills/video-transcript-downloader`
- `~/.codex/skills/whatsapp -> ~/Projects/agent-scripts/skills/whatsapp`
- `~/.codex/skills/wacli -> ~/Projects/agent-scripts/skills/wacli`

Do not replace this with a broad `~/.codex/skills -> ~/Projects/agent-scripts/skills` symlink unless intentionally changing Bram's setup.

Keep shared skills as real folders in `skills/`. Repo-owned skills stay canonical in their repo and are exposed here with tracked relative symlinks only when that repo exists locally, for example:

```text
skills/wacrawl -> ../../oss/wacrawl/.agents/skills/wacrawl
```

Optional crawler/messaging symlinks may be absent on Bram's machine; agents must check before use.

## Agent Instructions

Shared hard rules live in `AGENTS.MD`.

Global setup:
- `~/.codex/AGENTS.md -> ~/Projects/agent-scripts/AGENTS.MD`
- `~/.claude/CLAUDE.md -> ~/Projects/agent-scripts/AGENTS.MD`
- `~/.claude/AGENTS.md -> ~/Projects/agent-scripts/AGENTS.MD`

Downstream repos should use a pointer-style `AGENTS.MD`:

```text
READ ~/Projects/agent-scripts/AGENTS.MD BEFORE ANYTHING (skip if missing).
```

Repo-specific rules go below that pointer. Do not copy shared blocks into downstream repos.

## Helpers

`scripts/committer`
- Stages exactly the listed files.
- Enforces a non-empty commit message.
- Runs skill validation before committing.

`scripts/validate-skills`
- Checks every `skills/*/SKILL.md`.
- Verifies YAML front matter plus required `name` and `description`.
- Enable as a local hook with `git config core.hooksPath hooks`.

`scripts/docs-list.ts`
- Walks `docs/`.
- Enforces `summary` and `read_when` front matter.
- Prints onboarding summaries for repos that wire it in.

`scripts/gh-live-first`
- `gh` wrapper for Bram's PATH.
- Calls real Homebrew `gh` first, best-effort warms gitcrawl for cacheable reads, and falls back to `gitcrawl gh` only on outage/rate-limit for read commands.
- Use `GH_OFFLINE=1 gh ...` for explicit cache-only reads.

`scripts/github-offline-prewarm`
- Syncs local GitHub remotes into gitcrawl while GitHub is healthy.
- Keeps later `GH_OFFLINE=1 gh ...` reads useful during outages.

`config/bram-loop-repos.txt`
- Flagged repositories for `$bram-maintainer-loop` broad maintenance runs.
- Starts with `gohealthcli` and `gobankcli`; one repo slug per line.

`scripts/browser-tools.ts`
- Standalone Chrome DevTools helper.
- Common commands: `start --profile`, `nav <url>`, `eval '<js>'`, `screenshot`, `search --content "<query>"`, `content <url>`, `inspect`, `kill --all --force`.
- Build optional binary with `bun build scripts/browser-tools.ts --compile --target bun --outfile bin/browser-tools`.

## Syncing

Treat this repo as Bram's canonical shared agent setup and portable helper mirror.

Upstream intake from `steipete/agent-scripts`:
- Mine selectively; do not merge wholesale.
- Preserve Bram-local skills/helpers: `hermes-win`, `hermes-dashboard`, `autoreview`, `bram-maintainer-loop`, `tdd`, `to-prd`, `to-issues`, `grill-with-docs`.
- Skip or scrub non-Bram personal/product defaults before adopting docs or skills.
- Do not adopt symlinks to missing repos unless Bram explicitly configures them.
- Prefer generic helper/script fixes, CI smoke checks, and non-personal skill improvements.

When syncing downstream repos:
- Pull latest here first.
- Ensure each target repo starts with the pointer-style `AGENTS.MD`.
- Preserve repo-local rules below the pointer.
- Copy helper changes both directions only when the helper is meant to stay byte-identical.
- Keep scripts dependency-free and portable; no repo-specific imports or path aliases.

For submodules, repeat the pointer check inside each subrepo, push those changes, then bump submodule SHAs in the parent repo.
