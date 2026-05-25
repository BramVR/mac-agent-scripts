# Agent Scripts

This folder collects Bram's shared agent instructions, local skills, and small guardrail helpers for reuse across projects.

This repo is a BramVR-maintained fork of the original `steipete/agent-scripts` setup. Some skills and docs still preserve upstream provenance or optional Peter/OpenClaw-specific workflows; active shared defaults live in `AGENTS.MD`.

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
- `~/.codex/skills/video-transcript-downloader -> ~/Projects/agent-scripts/skills/video-transcript-downloader`
- `~/.codex/skills/gog -> ~/Projects/gogcli/.agents/skills/gog`
- `~/.codex/skills/codex-review -> ~/Projects/agent-scripts/skills/codex-review`
- `~/.codex/skills/to-prd -> ~/Projects/agent-scripts/skills/to-prd`

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

`scripts/browser-tools.ts`
- Standalone Chrome DevTools helper.
- Common commands: `start --profile`, `nav <url>`, `eval '<js>'`, `screenshot`, `search --content "<query>"`, `content <url>`, `inspect`, `kill --all --force`.
- Build optional binary with `bun build scripts/browser-tools.ts --compile --target bun --outfile bin/browser-tools`.

## Syncing

Treat this repo as Bram's canonical shared agent setup and portable helper mirror.

When syncing downstream repos:
- Pull latest here first.
- Ensure each target repo starts with the pointer-style `AGENTS.MD`.
- Preserve repo-local rules below the pointer.
- Copy helper changes both directions only when the helper is meant to stay byte-identical.
- Keep scripts dependency-free and portable; no repo-specific imports or path aliases.

For submodules, repeat the pointer check inside each subrepo, push those changes, then bump submodule SHAs in the parent repo.
