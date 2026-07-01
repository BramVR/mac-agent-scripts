# Vision

agent-scripts is Bram's shared agent instruction, skill, and helper-tool base. It should stay a terse, portable control plane for Codex-style work across projects, with skills as the canonical workflow layer and small scripts for repeatable guardrails.

## Merge by Default

- Small skill, script, prompt, and docs fixes that preserve Bram-local rules.
- New or updated skills with short quoted descriptions, valid front matter, and operational wording.
- Helper improvements that stay dependency-light, generic, and reusable across repos.
- GitHub, review, release, and maintainer-loop guardrail improvements with validation.
- Sync cleanup that mines upstream ideas while preserving Bram-specific behavior.

## Needs Sign-Off

- Broad rewrites of `AGENTS.MD` or global workflow policy.
- Replacing skill routing with copied long instructions in downstream repos.
- New secret, messaging, or external-service behavior without exact safety rules.
- Adopting upstream personal assumptions, broken symlinks, or non-Bram defaults.
- Changes that weaken `op`/1Password, Git, release, CI, or destructive-command guardrails.
