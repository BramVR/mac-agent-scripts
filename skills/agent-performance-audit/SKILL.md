---
name: agent-performance-audit
description: "Audit local Codex agent histories for a repository, record separate Claude activity coverage, compare correction and efficiency trends, and generate privacy-minimized JSON plus self-contained HTML. Use for Theo-style agent audits, monthly agent-performance checks, or post-issue-batch workflow reviews."
---

# Agent Performance Audit

Produce comparable Codex behavioral audits without copying raw conversations
into the report. Claude history contributes separate coverage counts, not the
Codex behavioral metrics. Keep source histories local and read-only.

## Run

1. Resolve the repository, an exact lowercase marker matching its repository
   basename, and an inclusive date window. The marker is a sanity check;
   histories are scoped by the target's canonical checkout path or normalized
   remote identity. Use a monthly window or the period since the previous major
   issue batch. Codex turns are included by task-start date and retained whole
   across date boundaries.
2. Use the task visualization directory for output. Identify the current audit
   task's session ID when available and pass `--exclude-session`; this validates
   that it contains a detectable audit turn but never drops the session's other
   turns. The script also detects audit turns by invocation/request markers.
3. Run:

   ```bash
   python3 <skill-dir>/scripts/audit_agent_history.py \
     --repo /absolute/repository/path \
     --marker repository-name \
     --since YYYY-MM-DD \
     --until YYYY-MM-DD \
     --output-dir /absolute/visualization/path
   ```

4. For a comparison, pass the previous generated JSON with `--baseline`.
5. Inspect aggregate results. Read raw surrounding history only for a small
   number of representative causal cases; keep those notes short and abstract.
   Never paste full messages, commands, outputs, or hidden instructions.
6. If causal notes materially improve the report, write a JSON array with
   `title`, `cause`, `control`, and `status`, then rerun with `--case-notes`.
7. Deliver the generated HTML link. Keep JSON beside it as reproducible evidence.

Run `python3 <skill-dir>/scripts/audit_agent_history.py --help` for all flags.

## Privacy Contract

- Emit aggregate counts, rates, tool categories, duration percentiles,
  category-only correction summaries, and concise causal notes only.
- Exclude injected AGENTS/skill/plugin/browser/environment/automation messages,
  explicit audit sessions, session IDs, source paths, cwd values, raw tool
  inputs/outputs, full user messages, and result excerpts.
- Redact URLs, emails, home paths, UUIDs, secret-shaped strings, and long hashes.
- Keep the HTML self-contained, script-free, under 512 KB, and free of local
  filesystem paths or private links.
- Do not upload or publish the report unless Bram explicitly requests it.

## Interpretation

- Correction detection favors precision and misses polite dissatisfaction.
- Nonzero shell output is not automatically agent error; separate test/build
  failures, probes, invocation errors, missing paths/modules, and permissions.
  Batched shell wrappers without per-command result envelopes are reported as
  uncovered and excluded from per-shell-output denominators.
- Token counts are model-accounted usage, not unique text or a billing estimate.
- Compare schema-2 datasets produced by this script for the same repository and
  matching-duration windows. Schema 2 derives each turn from cumulative Codex
  token deltas. Do not compare it directly with older one-off or schema-1 data.
- A local HTML report is diagnostic evidence, not a public performance claim.

## Cadence

Run monthly or after a major issue batch. Create a recurring automation only
when Bram explicitly requests scheduling.
