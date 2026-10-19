# Set up pstack

In this page you install the skills, pick which models pstack uses, and run your first task. Setup is one command plus a short conversation.

## Install the skills

From the agent-scripts checkout, run:

```bash
scripts/sync-skills --dry-run
scripts/sync-skills
```

The helper mirrors the skills into Codex's skill discovery directory.

## Pick your models

Run:

```text
$setup-pstack
```

[`$setup-pstack`](../../skills/setup-pstack/SKILL.md) detects the models you have access to, asks for a reasoning budget, shows you each role (code delegates, judgment, the review panels), and asks what you want. Answer the questions. It writes `${CODEX_HOME:-$HOME/.codex}/skills/poteto-mode/references/models.md`, a small role file the routed pstack skills read.

The defaults and reasoning budget are recorded in `${CODEX_HOME:-$HOME/.codex}/skills/poteto-mode/references/models.md`. `unlimited` keeps the role defaults. `large`, `medium`, and `small` select `xhigh`, `high`, and `medium` reasoning, within the configured model's supported efforts.

You only override what you care about. A role with no line in the rule keeps the skill's default. To restore a default, delete that role's line. A rerun of `$setup-pstack` keeps any role whose model differs from the default. When a default changes, a rule written before the change still pins the old default, so delete those role lines, or delete the file, then run `$setup-pstack` again.

You might be wondering what happens if you use Auto. Set a role to `inherit-parent` or `auto` and pstack omits the subagent `model` field, so the subagent inherits your parent chat model. Both values mean the same thing, and neither is a model slug. For a panel role the value is a list, and one subagent runs per entry, so the list length sets the panel size. Setup also configures `swarm workers`, the default model for every `$swarm` worker unless a race names a model for each arm.

## Use separate profiles in T3

The `t3-pstack` plugin normally shares one model sheet across Claude and Codex. The routing rule in [AGENTS.MD](../../AGENTS.MD) overrides that selection for this setup:

- Codex chats read `${CODEX_HOME:-$HOME/.codex}/t3-pstack-models.md`, linked to [the Codex profile](../../config/t3-pstack/codex-models.md).
- Claude chats read `${CLAUDE_CONFIG_DIR:-$HOME/.claude}/t3-pstack-models.md`, linked to [the Claude profile](../../config/t3-pstack/claude-models.md).

Both profiles live in this repository. Each profile has its own role models, reasoning settings, and panels. Setup changes only the current host's resolved profile. Keep both host links separate when rerunning the plugin's setup, which normally links both hosts to its shared sheet.

The Codex profile preserves the local Codex choices in T3 target syntax. Mixed panels still dispatch Claude entries through `claudeAgent` and GPT entries through `codex`. Standalone Codex continues to use the local port's role file above.

This selection is a user-instruction override, not a change to the plugin. It requires the shared `AGENTS.MD` routing rule to be loaded. Start a new chat after changing that rule.

## Accept the verification offer, or don't

At the end of setup, `$setup-pstack` looks for a way to prove app behavior in your project, either a `verify-*` skill or an existing harness. If it finds neither, it offers once to generate one with [`$create-verification-skill`](../../skills/create-verification-skill/SKILL.md).

Say yes and it writes `.agents/skills/verify-<app>/`, a project-local skill that teaches agents to drive your app the way a user does. It proves the skill works once before handing it over. Say no and setup moves on. You can run `$create-verification-skill` yourself any time. [Verify and ship](./06-verify-and-ship.md#create-a-project-verification-skill) covers it in depth.

If you're new to pstack, say yes. An agent that can check its own work keeps going until the check passes. An agent that can't hands every result back to you to check by hand. Of everything in this guide, the verification skill pays off the most.

After setup, start a new chat. The routed skills read the role file when they run.

## Keep the cost in check

pstack spends extra tokens on subagents and review panels. That's the price of the rigor. To spend fewer:

- Rerun `$setup-pstack` and pick a smaller reasoning budget or cheaper models. A strong model in the main chat with cheaper, faster models in the code roles is a good split.
- Set a role to `auto` or `inherit-parent` so it runs on the chat's own model.
- Shorten a panel list. Each entry runs one subagent.
- Save `$poteto-mode` for work that needs rigor. A small, obvious edit doesn't.

## Run your first task

Pick something real but small, and describe it the way you'd describe it to a colleague:

```text
$poteto-mode add a --json flag to this command. text output stays byte-identical. verify both.
```

Watch the todo list. Its first items are the matched playbook's steps copied in, the Feature playbook for this prompt. If `$poteto-mode` skips a step, the step stays in the list with `skip: <reason>`, so you can see what it chose not to do.

From here you can type normal follow-ups. Start each new task with `$poteto-mode` so Codex loads the skill and picks its playbook.

Next: [Route work through `$poteto-mode`](./02-poteto-mode.md).
