---
name: setup-matt-pocock-skills
description: "Configure this repo for the engineering skills: set up its issue tracker, triage label vocabulary, and domain doc layout. Run once before first use of the other engineering skills."
disable-model-invocation: true
---

# Setup Matt Pocock's Skills

_Source: [mattpocock/skills](https://github.com/mattpocock/skills), synced from `main` at `885e2ca4`; adapted to use Bram's canonical `AGENTS.MD` policy._

Scaffold the per-repo configuration that the engineering skills assume:

- **Issue tracker**: where issues live. GitHub is the default; local Markdown is also supported.
- **Triage labels**: the strings used for the five canonical triage roles.
- **Domain docs**: where `CONTEXT.md` and ADRs live, and the consumer rules for reading them.

This is a prompt-driven skill, not a deterministic script. Explore, present what you found, confirm with the user, then write.

## Process

### 1. Explore

Look at the current repo to understand its starting state. Read whatever exists; don't assume:

- `git remote -v` and `.git/config`: is this a GitHub repo? Which one?
- `AGENTS.MD` and `AGENTS.md` at the repo root: does either exist? Is there already an `## Agent skills` section?
- `CONTEXT.md` and `CONTEXT-MAP.md` at the repo root.
- `docs/adr/` and any `src/*/docs/adr/` directories.
- `docs/agents/`: does this skill's prior output already exist?
- `.scratch/`: a sign that a local-Markdown issue tracker convention is already in use.
- Is the `triage` skill installed? A `triage` skill folder beside this one or `triage` in the available skills decides whether section B runs.
- Monorepo signals: a `pnpm-workspace.yaml`, a `workspaces` field in `package.json`, or a populated `packages/*` with its own `src/`. These are present only in a genuinely large multi-package repo. Their absence means single-context, which fits almost every repo.

Ignore `CLAUDE.md`. Bram repositories use an AGENTS instruction file as canonical.

### 2. Present findings and ask

Summarize what's present and what's missing. Then take the sections in order. One section, one answer, then the next.

Lead each section with the recommended answer so the user can accept it in a word. Give a one-line explanation only when the choice genuinely branches. Skip the section when exploration already settled it, such as section B when `triage` isn't installed or section C when there is no monorepo.

**Section A: Issue tracker.**

> The issue tracker is where issues live for this repo. Skills such as `to-tickets`, `triage`, and `to-spec` read from and write to it. They need to know whether to call `gh issue create`, write a Markdown file under `.scratch/`, or follow another workflow.

Default posture: these skills were designed for GitHub. If a `git remote` points at GitHub, propose that. If a remote points at GitLab, propose GitLab. Otherwise, or if the user prefers, offer:

- **GitHub**: issues live in the repository's GitHub Issues and use the `gh` CLI.
- **GitLab**: issues live in GitLab Issues and use the [`glab`](https://gitlab.com/gitlab-org/cli) CLI.
- **Local Markdown**: issues live under `.scratch/<feature>/` in this repository.
- **Other**: ask the user to describe the workflow in one paragraph and record it as freeform prose.

Record the choice in `docs/agents/issue-tracker.md`. The GitHub and GitLab templates carry a "PRs as a request surface" flag, defaulted off. Leave it off and don't raise it. A user who wants external PRs in the triage queue can change the file later.

**Section B: Triage label vocabulary.** Skip this section if `triage` isn't installed.

If it is installed, ask exactly one question:

> Do you want to keep the default triage labels? Recommended: yes.

The defaults are the five canonical roles, each label string equal to its name: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`. On yes, write them as-is. Only if the user says no, usually because the tracker already uses other names, collect overrides so `triage` does not create duplicate labels.

**Section C: Domain docs.** Default to single-context, with one `CONTEXT.md` and `docs/adr/` at the repository root. Write it without asking.

Offer multi-context, with a root `CONTEXT-MAP.md` pointing to per-context `CONTEXT.md` files, only when exploration found monorepo signals. Then confirm which layout the user wants.

### 3. Confirm and edit

Show the user a draft of:

- The `## Agent skills` block for the repository's AGENTS file.
- `docs/agents/issue-tracker.md`.
- `docs/agents/domain.md`.
- `docs/agents/triage-labels.md`, only when `triage` is installed.

Let the user edit the draft before writing.

### 4. Write

Use the existing instruction file. Prefer `AGENTS.MD` when present, otherwise `AGENTS.md`. If neither exists, ask which casing to create. Never create or edit `CLAUDE.md`.

If an `## Agent skills` block already exists, update it in place. Do not overwrite surrounding user content.

The block:

```markdown
## Agent skills

### Issue tracker

[One-line summary of where issues are tracked]. See `docs/agents/issue-tracker.md`.

### Triage labels

[One-line summary of the label vocabulary]. See `docs/agents/triage-labels.md`.

### Domain docs

[One-line summary of the single-context or multi-context layout]. See `docs/agents/domain.md`.
```

Include the `### Triage labels` block and write `docs/agents/triage-labels.md` only when `triage` is installed and section B ran.

Use the seed templates in this skill folder:

- [issue-tracker-github.md](./issue-tracker-github.md): GitHub issue tracker.
- [issue-tracker-gitlab.md](./issue-tracker-gitlab.md): GitLab issue tracker.
- [issue-tracker-local.md](./issue-tracker-local.md): local-Markdown issue tracker.
- [triage-labels.md](./triage-labels.md): label mapping, only if `triage` is installed.
- [domain.md](./domain.md): domain doc consumer rules and layout.

For another issue tracker, write `docs/agents/issue-tracker.md` from the user's description.

### 5. Done

Report which files changed and which engineering skills will read them. The user can edit `docs/agents/*.md` directly later. Re-run this skill only to switch trackers or restart the setup.
