---
name: create-verification-skill
description: "Create a project-local Codex skill that launches and drives the real app to prove user-facing behavior. Use when a repo lacks a repeatable UI, CLI, TUI, API, mobile, or library verification workflow."
---

# Create a verification skill

Create a project-local skill that tells a fresh Codex agent how to launch the real app, exercise behavior through a user-facing entry point, capture evidence, and clean up safely. Write it for an agent arriving cold in the middle of a task.

## Inspect the repo

Read the project instructions and documented development commands first. Derive these facts from the checkout. Ask the user only for facts the repo cannot answer.

- User surface. Identify what users touch: web UI, CLI or TUI, desktop app, API, mobile app, or library. Pick the primary surface and note the others.
- Launch. Find the repo's own development or build command. Record ports, required environment names, fixtures, authentication, and a deterministic readiness signal.
- Drive. Prefer an existing Playwright or Cypress suite, expect script, PTY helper, debug port, API client, or project CLI. Otherwise choose the narrowest available Codex-capable route: browser automation for web and Electron, a PTY or tmux session for CLI and TUI, HTTP for services, or the platform's normal UI automation for native apps.
- Observe. Identify proof available from the real path: screenshots, accessibility snapshots, terminal transcripts, response bodies, exit codes, logs, files, database rows, or another user-facing read.
- Isolate. Determine whether concurrent runs can use separate ports, profiles, data directories, accounts, or fixture names. If isolation is impossible, make the generated skill refuse to drive an unverified shared instance.

Do not repair unrelated product code merely to make generation succeed. If the checkout cannot build or start, report the exact blocker and stop unless the user also authorized a product fix. Verification-only scaffolding may live inside the generated skill directory when it does not change production behavior.

## Choose the install location

Prefer the native `.agents/skills/verify-<app>` directory. Before creating its nested structure, check whether the current Codex filesystem policy permits a normal write under `.agents/skills`. Use one exact task-owned probe file and remove only that file after a successful check. Do not change permissions, flags, mounts, or ownership to force access.

If `.agents/skills` rejects the write, use `skills/verify-<app>` instead. Add or update a short `Local skills` entry in the nearest applicable `AGENTS.md` that tells a cold agent when to read the skill and gives its exact relative `SKILL.md` path. Keep existing project instructions intact. Do not request broader filesystem access solely to get the preferred location.

Call the selected directory `<skill-dir>` in the rest of this workflow. Mention a fallback and its cause in the handoff. If neither location is writable, report the blocker and stop.

## Generate the project skill

Write `<skill-dir>/SKILL.md`. Use lowercase letters, digits, and hyphens for `<app>`. Add valid YAML frontmatter with `name: verify-<app>` and a short description naming the app, user surface, and useful trigger.

Ground every instruction in this repo. Leave no placeholder commands, ports, selectors, paths, or environment names. Include these sections:

- Launch. Exact setup and launch commands, readiness check, ownership recording, and teardown. For a short-lived CLI or TUI, build or install once, then start each drive in a fresh isolated PTY or tmux session.
- Doctor. One read-only check that answers whether the instance is safe and useful to drive. Check the facts that matter, such as process identity, expected build, owned port, disposable data path, or valid authentication.
- Drive. Exact commands and stable handles from the app. Prefer roles, accessible names, data attributes, prompt text, route paths, and structured output over coordinates or tab order. Name the Codex tool, skill, connector, or repo helper the recipe requires.
- Evidence. Name the artifact directory and required proof for each kind of behavior. Capture both the user action and resulting state. Confirm durable side effects through a second read. Use mocks only at an existing production boundary. For dry-run or test modes, observe what they skip instead of trusting the label.
- Cleanup. Stop only the exact processes the run started. Record process identity before teardown. Remove task-owned scratch state, never shared state or evidence. Confirm evidence remains and the worktree has no unexpected verification residue.
- Helpers. Document every owned helper's invocation. Make scripts executable. Keep helpers inside the generated skill directory unless the repo already has a canonical harness location and the user asked to integrate there.

Add `agents/openai.yaml` when UI metadata will help discovery. Its `default_prompt` must mention `$verify-<app>`. Do not disable implicit invocation unless the user asks.

## Seed the feature map

Create `<skill-dir>/features/README.md` and one file for each of the three to five most important user-facing features you can prove from routes, commands, menus, tests, or docs. Read [`references/feature-map-example/`](references/feature-map-example/) before writing the map.

Each feature file explains the behavior from the user's point of view, every known entry point, exact drive commands, the observable success state, and run-invalidating traps. Use these four H2 sections in order:

1. `Sub-features`
2. `How to get to it (user POV)`
3. `Driving it with <tool or harness>`
4. `Gotchas`

The map is a verification contract. Do not mark one entry point verified because a different entry point worked. Record unmet prerequisites and attempted routes for anything unreachable.

## Prove the generated skill

Run the generated instructions once from start to finish:

1. Launch the app in isolated verification state.
2. Run doctor and require it to pass.
3. Drive one mapped feature through a real user entry point.
4. Capture the named evidence and verify any side effect through a second view.
5. Run cleanup, then confirm the evidence still exists and no task-owned process or scratch state remains.

After any failed attempt, run the generated cleanup before revising and retrying. If safe execution needs credentials, production mutation, unavailable hardware, or broader authorization, stop with the generated draft and name the unproved step. Never describe an unexecuted skill as verified.

## Handoff

Report the generated skill path, mapped features, exact path exercised, evidence location, cleanup result, and any unreachable prerequisites. Point to `$maintain-verification-skill` for a future source-plus-live audit when the app changes materially.
