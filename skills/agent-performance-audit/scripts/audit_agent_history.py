#!/usr/bin/env python3
"""Generate a privacy-minimized repository Codex-performance audit."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import re
import shlex
import statistics
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

VERSION = "1.0.0"
SCHEMA_VERSION = 2
MAX_HTML_BYTES = 512 * 1024
INJECTED_PREFIXES = (
    "<recommended_plugins>",
    "<skill>",
    "<app-context>",
    "<in-app-browser-context",
    "<environment_context>",
    "<codex_delegation>",
    "<automation",
    "<heartbeat>",
    "<system-reminder>",
    "Base directory for this skill:",
    "# AGENTS.md instructions",
    "<INSTRUCTIONS>",
)
REQUEST_MARKERS = ("# My request for Codex:", "## My request:")
AUDIT_SESSION_RE = re.compile(
    r"\$agent-performance-audit|"
    r"(?:run|perform|generate|create|do|start|rerun|compare).{0,60}"
    r"(?:agent-performance-audit|agent performance audit)|"
    r"(?:python(?:3)?\s+)?(?:\S*[\\/])?(?:audit_agent_history|audit_history)\.py"
    r".{0,120}(?:--repo|--since|--output-dir)|"
    r"audit.{0,30}agent performance|"
    r"monthly.{0,30}agent[- ]performance check|"
    r"post[- ]issue[- ]batch.{0,30}workflow review|"
    r"(?:theo.?style|full).{0,30}agent(?: performance)? audit",
    re.IGNORECASE,
)
AUDIT_FOLLOWUP_RE = re.compile(
    r"^(?:(?:please|can you|could you|would you)\s+)?"
    r"(?:(?:continue|rerun|retry|compare|use|update|fix|open).{0,60}"
    r"(?:audit|baseline|agent performance)|"
    r"(?:include|add|remove|exclude|show|filter|break down).{0,80}"
    r"(?:audit|baseline|agent performance|"
    r"january|february|march|april|may|june|july|august|september|"
    r"october|november|december))\b",
    re.IGNORECASE,
)
AUDIT_FEEDBACK_RE = re.compile(
    r"\b(?:audit|baseline|agent performance|audit report|"
    r"performance report|this report)s?\b",
    re.IGNORECASE,
)
CORRECTION_GATE = re.compile(
    r"\bwrong\b|incorrect|doesn['’]?t work|does not work|not working|\bbroken\b|"
    r"\bbuggy\b|(?:again.{0,40}(?:no |error|wrong|fail)|(?:error|wrong|fail).{0,40}again)|"
    r"\bstill\b.{0,80}(?:broken|fail|wrong|not|doesn)|you (?:did|forgot|missed|stopped|broke|hide)|"
    r"not what i|didn['’]?t ask|did not ask|too complex|too strict|overcomplicat|\bregression\b|"
    r"few issues|one thing .{0,60}does not|do not want to limit|does not always|"
    r"not good visible|undo does not work|out of scope|unasked",
    re.IGNORECASE,
)
CORRECTION_DIRECTED_RE = re.compile(
    r"\b(?:you|your|still|again)\b|"
    r"not what i|didn['’]?t ask|did not ask|out of scope|unasked|"
    r"keep going|don['’]?t stop|do not stop",
    re.IGNORECASE,
)
MANUAL_ACCEPTANCE_RE = re.compile(
    r"(?:open|show|leave|make) .{0,50}maya.{0,80}(?:test|verify)|"
    r"(?:test|verify) .{0,60}(?:myself|manually)|what (?:i|we) need to (?:test|verify)|"
    r"visual proof|screenshot proof",
    re.IGNORECASE,
)
CORRECTION_PATTERNS = {
    "wrong_result": re.compile(
        r"\bwrong\b|incorrect|doesn['’]?t work|does not work|not working|\bbroken\b|"
        r"implemented .{0,40}wrong|changed .{0,40}wrong",
        re.IGNORECASE,
    ),
    "misread_scope": re.compile(
        r"not what i (?:asked|meant)|i (?:asked|said) .{0,100}(?:not|only)|"
        r"didn['’]?t ask|did not ask|you misunderstood|only asked|out of scope|unasked|"
        r"why did you|instead of",
        re.IGNORECASE,
    ),
    "premature_stop": re.compile(
        r"keep going|continue (?:working|with|until|the)|don['’]?t stop|do not stop|"
        r"you stopped|finish (?:it|this|the)|not done|full .{0,30}(?:audit|review|report)|"
        r"complete .{0,30}(?:audit|review|report)",
        re.IGNORECASE,
    ),
    "verification_gap": re.compile(
        r"did you (?:test|verify|check|run)|have you (?:test|verified|checked|run)|"
        r"(?:test|verify|check) (?:it|this|that|the actual)|actual maya|real maya|"
        r"visual proof|e2e proof|screenshot proof",
        re.IGNORECASE,
    ),
    "regression": re.compile(
        r"\bregression\b|used to work|you broke|broke .{0,50}(?:test|ui|scene|workflow)|"
        r"still fail|now fail",
        re.IGNORECASE,
    ),
    "overbuild": re.compile(
        r"too complex|overbuild|overcomplicat|simpler|yagni|scope creep|unnecessary complexity",
        re.IGNORECASE,
    ),
    "process_safety": re.compile(
        r"(?:killed|kill|stopped) .{0,40}process|secret|private data|user data|"
        r"deleted .{0,40}(?:file|branch|worktree|data)|destructive",
        re.IGNORECASE,
    ),
    "pr_hygiene": re.compile(
        r"(?:wrong|forgot|missed|should|must|don['’]?t|do not).{0,80}"
        r"(?:draft pr|pull request|merge request|commit|push|branch)",
        re.IGNORECASE,
    ),
    "ui_quality": re.compile(
        r"looks? wrong|doesn['’]?t look|ui .{0,50}(?:wrong|broken|bad)|"
        r"(?:wrong|broken|bad).{0,50}(?:button|layout|panel|dialog|screenshot)",
        re.IGNORECASE,
    ),
}
PREFIXED_SECRET_RE = re.compile(
    r"\b(?:sk-[A-Za-z0-9_-]{8,}|sk_(?:live|test)_[A-Za-z0-9_-]{8,}|"
    r"gh[pousr]_[A-Za-z0-9_]{8,}|"
    r"github_pat_[A-Za-z0-9_]{8,}|xox[baprs]-[A-Za-z0-9_-]{8,}|"
    r"xapp-[A-Za-z0-9_-]{8,}|glpat-[A-Za-z0-9_-]{8,}|"
    r"npm_[A-Za-z0-9_-]{8,}|AIza[A-Za-z0-9_-]{35}|"
    r"[A-Za-z][A-Za-z0-9]{0,12}_(?:live|test|prod)_[A-Za-z0-9_-]{8,})\b",
    re.IGNORECASE,
)
AWS_ACCESS_KEY_RE = re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b")
JWT_RE = re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b")
BEARER_RE = re.compile(
    r"\b(?:authorization\s*:\s*)?bearer\s+[A-Za-z0-9._~+/=-]{8,}",
    re.IGNORECASE,
)
BASIC_AUTH_RE = re.compile(
    r"\bauthorization\s*:\s*basic\s+[A-Za-z0-9+/=]{8,}",
    re.IGNORECASE,
)
ASSIGNED_SECRET_RE = re.compile(
    r"(?<![A-Za-z0-9])(?:(?:[\"']?)(?:[A-Za-z0-9]+[_-])*"
    r"(?:password|passwd|pwd|secret|token|"
    r"passcode|pin|secret[\s_-]?key|api[\s_-]?key|access[\s_-]?key)|"
    r"database[_-]?url|db[_-]?url|"
    r"connection[_-]?string)(?:[\"']?)"
    r"\s*[:=]\s*(?:\"[^\"]+\"|'[^']+'|[^\r\n,;}{\"']+)",
    re.IGNORECASE,
)
NATURAL_SECRET_RE = re.compile(
    r"\b(?:password|passwd|passcode|pin|"
    r"api[\s_-]+key|access[\s_-]+key|"
    r"secret[\s_-]+key)\s+(?:is\s+)?"
    r"(?:\"[^\"]+\"|'[^']+'|[^\r\n,;}{\"']+)",
    re.IGNORECASE,
)
CREDENTIAL_URI_RE = re.compile(
    r"\b(?:postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis|amqp)://[^\s<>\"']+",
    re.IGNORECASE,
)
PRIVATE_KEY_RE = re.compile(
    r"-----BEGIN (?:OPENSSH |RSA |EC |DSA |ENCRYPTED )?PRIVATE KEY-----"
    r".*?(?:-----END (?:OPENSSH |RSA |EC |DSA |ENCRYPTED )?PRIVATE KEY-----|$)",
    re.IGNORECASE | re.DOTALL,
)
SECRET_PATTERNS = (
    PREFIXED_SECRET_RE,
    AWS_ACCESS_KEY_RE,
    JWT_RE,
    BEARER_RE,
    BASIC_AUTH_RE,
    ASSIGNED_SECRET_RE,
    NATURAL_SECRET_RE,
    CREDENTIAL_URI_RE,
    PRIVATE_KEY_RE,
)
ABSOLUTE_PATH_RE = re.compile(
    r"(?<![\w/.<])/(?!/)(?=[^\s/<>\"'])[^\n<>\"']+|"
    r"\b[A-Za-z]:[\\/][^\n<>\"']+|\\\\[^\\\s]+\\[^\n<>\"']+",
    re.IGNORECASE,
)
HOME_PATH_RE = re.compile(
    r"(?<![\w])(?:~|\$(?:HOME|USERPROFILE)|%(?:HOME|USERPROFILE)%)[\\/]\S+",
    re.IGNORECASE,
)
RELATIVE_PATH_RE = re.compile(
    r"(?<![\w:/.])(?:"
    r"(?:\.\.?[\\/])+(?:[^\s\\/<>\"']+[\\/]?)+|"
    r"(?:[^\s\\/<>\"']+[\\/])+[^\s\\/<>\"']+"
    r")",
    re.IGNORECASE,
)
LABELED_ID_RE = re.compile(
    r"\b(?:session|thread|host|run|task)[_-]?(?:id)?[\"']?\s*"
    r"(?:[:=]|\bid\b)\s*[\"']?[A-Za-z0-9._:-]{2,}[\"']?",
    re.IGNORECASE,
)
EMAIL_RE = re.compile(r"\b[\w.+-]+@[^\s@<>\"']+\b", re.UNICODE)
HOSTNAME_RE = re.compile(
    r"\b(?:www\.)?(?:[A-Za-z0-9-]{1,63}\.)+(?:internal|local|test|example|"
    r"invalid|localhost|[A-Za-z]{2,63})(?:[/:][^\s<>\"']*)?",
    re.IGNORECASE,
)
PRIVATE_IP_RE = re.compile(
    r"\b(?:10(?:\.\d{1,3}){3}|192\.168(?:\.\d{1,3}){2}|"
    r"172\.(?:1[6-9]|2\d|3[01])(?:\.\d{1,3}){2}|"
    r"127(?:\.\d{1,3}){3})(?::\d{1,5})?\b"
)
PRIVACY_REPLACEMENTS = (
    (re.compile(r"file://\S+", re.IGNORECASE), "[local-url]"),
    (re.compile(r"\b[A-Za-z][A-Za-z0-9+.-]*://\S+"), "[url]"),
    (HOME_PATH_RE, "[path]"),
    (ABSOLUTE_PATH_RE, "[path]"),
    (RELATIVE_PATH_RE, "[path]"),
    (EMAIL_RE, "[email]"),
    (
        re.compile(
            r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b",
            re.IGNORECASE,
        ),
        "[id]",
    ),
    (LABELED_ID_RE, "[id]"),
    *((pattern, "[secret]") for pattern in SECRET_PATTERNS),
    (PRIVATE_IP_RE, "[private-ip]"),
    (HOSTNAME_RE, "[host]"),
    (re.compile(r"\b[0-9a-f]{32,}\b", re.IGNORECASE), "[hash]"),
)
COMPARISON_KEYS = (
    "sessions",
    "human_messages",
    "correction_messages",
    "corrections_per_100_messages",
    "shell_invocation_errors",
    "shell_invocation_errors_per_100_tool_outputs",
    "automation_turns",
    "automation_token_share_percent",
    "agent_history_read_calls",
)
TOKEN_KEYS = (
    "input_tokens",
    "cached_input_tokens",
    "output_tokens",
    "reasoning_output_tokens",
    "total_tokens",
)
TEST_BUILD_COMMAND_RE = re.compile(
    r"\b(?:pytest|ctest|mypy|unittest|jest|autoreview)\b|"
    r"\bruff\s+check\b|\bmaya.?stall\b|\bbuild\.bat\b|\bcmake\s+--build\b|"
    r"\bnpm\s+(?:run\s+)?test\b|\bpnpm\s+(?:run\s+)?test\b|"
    r"\byarn\s+test\b|\bcargo\s+test\b|\bgo\s+test\b|\bdotnet\s+test\b",
    re.IGNORECASE,
)


class AuditError(RuntimeError):
    """Expected audit configuration or data failure."""


def safe_model_label(value: Any) -> str:
    return re.sub(r"[\\/]+", ":", str(value or "unknown"))


@dataclass(frozen=True)
class RepositoryScope:
    path: Path
    remote: str
    accepted_markers: frozenset[str]

    @property
    def identity(self) -> str:
        value = self.remote or str(self.path)
        return hashlib.sha256(value.encode()).hexdigest()[:24]


@dataclass
class SessionAudit:
    started_day: str
    dominant_model: str
    human_messages: int
    message_models: Counter[str]
    corrections: list[dict[str, Any]]
    manual_acceptance: int
    tool_categories: Counter[str]
    tool_calls: int
    shell_outputs: int
    shell_failures: int
    shell_failure_categories: Counter[str]
    batched_shell_wrappers_uncovered: int
    process_kills: int
    personal_folder_reads: int
    agent_history_reads: int
    test_calls: int
    substantive_durations_ms: list[int]
    automation_durations_ms: list[int]
    substantive_usage: Counter[str]
    automation_usage: Counter[str]
    substantive_turns: int
    automation_turns: int
    timeline: dict[str, Counter[str]]


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    try:
        with path.open(errors="replace") as handle:
            for line in handle:
                try:
                    value = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(value, dict):
                    rows.append(value)
    except OSError:
        return []
    return rows


def text_from_content(content: Any) -> str:
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return ""
    parts = []
    for item in content:
        if isinstance(item, dict) and item.get("type") in {
            "input_text",
            "output_text",
            "text",
        }:
            parts.append(str(item.get("text", "")))
    return "\n".join(parts)


def clean_user_text(text: str) -> str:
    for marker in REQUEST_MARKERS:
        if marker in text:
            text = text.rsplit(marker, 1)[1]
            break
    text = re.sub(
        r"<image\b[^>]*>.*?</image>", "", text, flags=re.IGNORECASE | re.DOTALL
    )
    injected_tags = {
        prefix[1:-1]
        for prefix in INJECTED_PREFIXES
        if prefix.startswith("<") and prefix.endswith(">") and " " not in prefix
    }
    injected_tags.update(
        prefix[1:].split()[0]
        for prefix in INJECTED_PREFIXES
        if prefix.startswith("<") and not prefix.endswith(">")
    )
    for tag in injected_tags:
        text = re.sub(
            rf"<{re.escape(tag)}\b[^>]*>.*?</{re.escape(tag)}>",
            "",
            text,
            flags=re.IGNORECASE | re.DOTALL,
        )
    stripped = text.strip()
    if stripped.startswith(INJECTED_PREFIXES):
        return ""
    return stripped


def redact(text: str, limit: int = 180) -> str:
    value = re.sub(r"```.*?```", "[code]", text, flags=re.DOTALL)
    for pattern, replacement in PRIVACY_REPLACEMENTS:
        value = pattern.sub(replacement, value)
    value = re.sub(r"\s+", " ", value).strip()
    return value if len(value) <= limit else value[: limit - 1] + "…"


def parse_day(raw: str | None, flag: str) -> date | None:
    if raw is None:
        return None
    try:
        return date.fromisoformat(raw)
    except ValueError as error:
        raise AuditError(f"{flag} must use YYYY-MM-DD: {raw!r}") from error


def in_window(timestamp: str, since: date | None, until: date | None) -> bool:
    try:
        day = date.fromisoformat(timestamp[:10])
    except ValueError:
        return since is None and until is None
    return (since is None or day >= since) and (until is None or day <= until)


def rows_in_date_window(
    rows: list[dict[str, Any]], since: date | None, until: date | None
) -> list[dict[str, Any]]:
    if since is None and until is None:
        return rows
    return [
        row
        for row in rows
        if row.get("timestamp") and in_window(str(row["timestamp"]), since, until)
    ]


def row_turn_id(row: dict[str, Any], active_turn: str = "") -> str:
    payload = row.get("payload", {}) or {}
    passthrough = payload.get("internal_chat_message_metadata_passthrough", {}) or {}
    return str(payload.get("turn_id") or passthrough.get("turn_id") or active_turn)


def cumulative_turn_usage(rows: list[dict[str, Any]]) -> dict[str, Counter[str]]:
    """Return per-turn deltas from cumulative Codex token snapshots."""
    last_total: Counter[str] = Counter()
    baselines: dict[str, Counter[str]] = {}
    result: dict[str, Counter[str]] = {}
    current_turn = ""
    for row in rows:
        if row.get("type") != "event_msg":
            continue
        payload = row.get("payload", {}) or {}
        event_type = payload.get("type")
        if event_type == "task_started":
            current_turn = row_turn_id(row)
            baselines[current_turn] = last_total.copy()
        elif event_type == "token_count":
            total = (payload.get("info") or {}).get("total_token_usage") or {}
            if total:
                last_total = Counter(
                    {key: int(total.get(key) or 0) for key in TOKEN_KEYS}
                )
                if current_turn:
                    baseline = baselines.get(current_turn, Counter())
                    result[current_turn] = Counter(
                        {
                            key: max(0, last_total[key] - baseline[key])
                            for key in TOKEN_KEYS
                        }
                    )
        elif event_type == "task_complete":
            current_turn = ""
    return result


def codex_turns_in_window(
    rows: list[dict[str, Any]],
    since: date | None,
    until: date | None,
    excluded_turns: set[str] | None = None,
) -> list[dict[str, Any]]:
    """Include complete Codex turns whose task-start timestamp is in the window."""
    excluded_turns = excluded_turns or set()
    included_turns = {
        row_turn_id(row)
        for row in rows
        if row.get("type") == "event_msg"
        and (row.get("payload", {}) or {}).get("type") == "task_started"
        and row.get("timestamp")
        and in_window(str(row["timestamp"]), since, until)
        and row_turn_id(row) not in excluded_turns
    }
    inferred_turns = turn_ids_by_row(rows)
    return [
        row
        for row, turn_id in zip(rows, inferred_turns, strict=True)
        if turn_id in included_turns
    ]


def turn_ids_by_row(rows: list[dict[str, Any]]) -> list[str]:
    """Associate untagged rows with the surrounding or following task boundary."""
    result = [""] * len(rows)
    active_turn = ""
    pending: list[int] = []
    for index, row in enumerate(rows):
        payload = row.get("payload", {}) or {}
        event_type = payload.get("type") if row.get("type") == "event_msg" else ""
        explicit = row_turn_id(row)
        if event_type == "task_started":
            active_turn = explicit
            for pending_index in pending:
                result[pending_index] = active_turn
            pending.clear()
        turn_id = explicit or active_turn
        if turn_id:
            result[index] = turn_id
        elif event_type != "task_complete":
            pending.append(index)
        if event_type == "task_complete":
            active_turn = ""
    return result


def has_prior_human_message(
    all_rows: list[dict[str, Any]],
    selected_rows: list[dict[str, Any]],
    excluded_turns: set[str] | None = None,
) -> bool:
    if not selected_rows:
        return False
    first_selected = next(
        (index for index, row in enumerate(all_rows) if row is selected_rows[0]), 0
    )
    inferred_turns = turn_ids_by_row(all_rows)
    excluded_turns = excluded_turns or set()
    for index, row in enumerate(all_rows[:first_selected]):
        if inferred_turns[index] in excluded_turns:
            continue
        if row.get("type") != "response_item":
            continue
        payload = row.get("payload", {}) or {}
        if payload.get("type") != "message" or payload.get("role") != "user":
            continue
        if clean_user_text(text_from_content(payload.get("content"))):
            return True
    return False


def first_metadata(path: Path) -> dict[str, Any]:
    try:
        with path.open(errors="replace") as handle:
            first = json.loads(handle.readline())
    except (OSError, json.JSONDecodeError):
        return {}
    return first.get("payload", {}) if isinstance(first, dict) else {}


def deduplicated_codex_files(roots: Iterable[Path]) -> list[Path]:
    by_session: dict[str, Path] = {}
    for root in roots:
        if not root.is_dir():
            continue
        for path in sorted(root.rglob("*.jsonl"), key=str):
            metadata = first_metadata(path)
            session_id = str(
                metadata.get("session_id") or metadata.get("id") or path.stem
            )
            current = by_session.get(session_id)
            try:
                size = path.stat().st_size
                current_size = current.stat().st_size if current is not None else -1
                larger = size > current_size or (
                    size == current_size
                    and current is not None
                    and str(path) < str(current)
                )
            except OSError:
                continue
            if larger:
                by_session[session_id] = path
    return sorted(by_session.values(), key=str)


def normalize_remote(value: str) -> str:
    remote = value.strip().rstrip("/\\").removesuffix(".git")
    remote = re.sub(r"^[A-Za-z][A-Za-z0-9+.-]*://(?:[^@/]+@)?", "", remote)
    remote = re.sub(r"^[^@/]+@([^:]+):", r"\1/", remote)
    return remote.lower()


def repository_scope(repo: Path, markers: list[str]) -> RepositoryScope:
    top_level = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "--show-toplevel"],
        check=False,
        capture_output=True,
        text=True,
    )
    if top_level.returncode != 0:
        raise AuditError(f"--repo must be a Git worktree: {repo}")
    canonical = Path(top_level.stdout.strip()).resolve()
    if canonical != repo:
        raise AuditError(f"--repo must be the Git top-level: {canonical}")
    result = subprocess.run(
        ["git", "-C", str(repo), "remote", "get-url", "origin"],
        check=False,
        capture_output=True,
        text=True,
    )
    remote = normalize_remote(result.stdout) if result.returncode == 0 else ""
    accepted = {repo.name.lower()}
    if remote:
        accepted.add(remote.rsplit("/", 1)[-1])
    unexpected = sorted(set(markers) - accepted)
    if unexpected:
        raise AuditError(
            "--marker must exactly match the target repository basename: "
            + ", ".join(unexpected)
        )
    return RepositoryScope(repo, remote, frozenset(accepted))


def matches_repository(metadata: dict[str, Any], scope: RepositoryScope) -> bool:
    git = metadata.get("git", {}) or {}
    history_remote = normalize_remote(str(git.get("repository_url") or ""))
    if scope.remote and history_remote:
        return history_remote == scope.remote
    raw_cwd = str(metadata.get("cwd") or "")
    if not raw_cwd:
        return False
    cwd = Path(raw_cwd).expanduser().resolve()
    return cwd == scope.path or scope.path in cwd.parents


def audit_turn_ids(rows: list[dict[str, Any]]) -> set[str]:
    result: set[str] = set()
    audit_workflow_active = False
    inferred_turns = turn_ids_by_row(rows)
    for row, inferred_turn in zip(rows, inferred_turns, strict=True):
        payload = row.get("payload", {}) or {}
        if row.get("type") != "response_item":
            continue
        if payload.get("type") != "message" or payload.get("role") != "user":
            continue
        text = clean_user_text(text_from_content(payload.get("content")))
        if not text:
            continue
        explicit_audit = bool(AUDIT_SESSION_RE.search(text))
        if explicit_audit:
            audit_workflow_active = True
        elif audit_workflow_active and not (
            AUDIT_FOLLOWUP_RE.search(text)
            or (AUDIT_FEEDBACK_RE.search(text) and CORRECTION_GATE.search(text))
        ):
            audit_workflow_active = False
        if audit_workflow_active:
            turn_id = row_turn_id(row, inferred_turn)
            if turn_id:
                result.add(turn_id)
    return result


def session_is_audit(rows: list[dict[str, Any]]) -> bool:
    return bool(audit_turn_ids(rows))


def audit_turns_in_window(
    rows: list[dict[str, Any]],
    excluded_turns: set[str],
    since: date | None,
    until: date | None,
) -> set[str]:
    return {
        row_turn_id(row)
        for row in rows
        if row.get("type") == "event_msg"
        and (row.get("payload", {}) or {}).get("type") == "task_started"
        and row_turn_id(row) in excluded_turns
        and row.get("timestamp")
        and in_window(str(row["timestamp"]), since, until)
    }


def validate_explicit_exclusions(requested: set[str], matched: set[str]) -> None:
    unmatched = requested - matched
    if unmatched:
        raise AuditError(
            "--exclude-session did not match a scoped audit session: "
            + ", ".join(sorted(unmatched))
        )


def validate_artifact_paths(
    repo: Path,
    output_dir: Path,
    baseline: Path | None,
    case_notes: Path | None,
) -> None:
    if output_dir == repo or repo in output_dir.parents:
        raise AuditError("--output-dir must be outside the repository")
    output_paths = {
        output_dir / "agent-performance-audit.json",
        output_dir / "agent-performance-audit.html",
    }
    for option, input_path in (
        ("--baseline", baseline),
        ("--case-notes", case_notes),
    ):
        if input_path and input_path.expanduser().resolve() in output_paths:
            raise AuditError(f"{option} must not be overwritten by an output artifact")


def shell_failure_category(command: str, output: str) -> str:
    lowered = command.lower()
    if re.search(
        r"command not found|unbound variable|shell parse error",
        output,
        re.IGNORECASE,
    ):
        return "invocation_error"
    if TEST_BUILD_COMMAND_RE.search(command):
        return "test_or_build"
    if re.search(
        r"syntax error|parse error",
        output,
        re.IGNORECASE,
    ):
        return "invocation_error"
    if re.search(
        r"no such file|module not found|modulenotfound|cannot find",
        output,
        re.IGNORECASE,
    ):
        return "missing_path_or_module"
    if "permission denied" in output.lower():
        return "permission"
    if re.search(r"\brg\b|git diff --quiet|git merge-base --is-ancestor", lowered):
        return "probe_or_no_match"
    return "other_nonzero"


def tool_category(name: str, raw_input: str) -> str:
    identity = name.lower()
    base = identity.rsplit("__", 1)[-1].rsplit(".", 1)[-1]
    if base in {"exec_command", "write_stdin"} or identity == "exec":
        return "shell"
    if base == "apply_patch":
        return "file_edit"
    if base in {"wait_threads", "read_thread", "list_threads"}:
        return "thread_coordination"
    if "automation" in identity:
        return "automation"
    if "github" in identity or base == "gh":
        return "github"
    if "browser" in identity or "web__" in identity or "playwright" in identity:
        return "browser_web"
    if "peekaboo" in identity or "view_image" in identity or "imagegen" in identity:
        return "visual_ui"
    return "other"


def tool_categories_for_call(name: str, raw_input: str) -> list[str]:
    return [
        tool_category(tool_name, raw_input)
        for tool_name in tool_names_for_call(name, raw_input)
    ]


def tool_names_for_call(name: str, raw_input: str) -> list[str]:
    identity = name.lower()
    base = identity.rsplit("__", 1)[-1].rsplit(".", 1)[-1]
    if base == "exec" and "." in identity:
        wrapped = re.findall(r"\btools\.([A-Za-z0-9_]+)\s*\(", raw_input)
        if wrapped:
            return wrapped
    return [name]


def shell_commands(call: dict[str, str]) -> list[str]:
    if "shell" not in tool_categories_for_call(call["name"], call["input"]):
        return []
    raw = call["input"]
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        parsed = None
    if isinstance(parsed, dict) and isinstance(parsed.get("cmd"), str):
        return [parsed["cmd"]]
    commands = []
    for match in re.finditer(r'(?:["\']cmd["\']|\bcmd)\s*:\s*("(?:\\.|[^"\\])*")', raw):
        try:
            command = json.loads(match.group(1))
        except json.JSONDecodeError:
            continue
        if isinstance(command, str):
            commands.append(command)
    return commands


def structured_exit_code(output: str) -> int | None:
    try:
        parsed = json.loads(output)
    except json.JSONDecodeError:
        parsed = None
    if isinstance(parsed, dict):
        exit_code = parsed.get("exit_code")
        if isinstance(exit_code, int):
            return exit_code
        if parsed.get("isError") is True or parsed.get("is_error") is True:
            return 1
    match = re.search(
        r"(?m)^(?:Process|Command|Script) exited with code ([0-9]+)\s*$", output
    )
    return int(match.group(1)) if match else None


def structured_result_envelopes(output: str) -> list[str]:
    try:
        parsed = json.loads(output)
    except json.JSONDecodeError:
        return []
    results: list[str] = []

    def collect(value: Any) -> None:
        if isinstance(value, dict):
            if isinstance(value.get("exit_code"), int):
                results.append(json.dumps(value, sort_keys=True))
                return
            for nested in value.values():
                collect(nested)
        elif isinstance(value, list):
            for nested in value:
                collect(nested)

    collect(parsed)
    return results


def elapsed_milliseconds(start: str, end: str) -> int:
    if not start or not end:
        return 0
    try:
        started = datetime.fromisoformat(start.replace("Z", "+00:00"))
        completed = datetime.fromisoformat(end.replace("Z", "+00:00"))
    except ValueError:
        return 0
    return max(0, int((completed - started).total_seconds() * 1000))


def session_id_from_output(output: str) -> str:
    try:
        parsed = json.loads(output)
    except json.JSONDecodeError:
        parsed = None
    if isinstance(parsed, dict) and parsed.get("session_id") is not None:
        return str(parsed["session_id"])
    match = re.search(r'"session_id"\s*:\s*([0-9]+)', output)
    return match.group(1) if match else ""


def session_id_from_input(raw: str) -> str:
    match = re.search(r'(?:["\']session_id["\']|\bsession_id)\s*:\s*([0-9]+)', raw)
    return match.group(1) if match else ""


def cell_id_from_output(output: str) -> str:
    try:
        parsed = json.loads(output)
    except json.JSONDecodeError:
        parsed = None
    if isinstance(parsed, dict) and parsed.get("cell_id") is not None:
        return str(parsed["cell_id"])
    match = re.search(r'"cell_id"\s*:\s*"?([A-Za-z0-9_-]+)', output)
    if not match:
        match = re.search(r"\bcell ID ([A-Za-z0-9_-]+)", output, re.IGNORECASE)
    return match.group(1) if match else ""


def cell_id_from_input(raw: str) -> str:
    match = re.search(
        r'(?:["\']cell_id["\']|\bcell_id)\s*:\s*["\']?([A-Za-z0-9_-]+)',
        raw,
    )
    return match.group(1) if match else ""


def write_stdin_chars(call: dict[str, str]) -> list[str]:
    if not any(
        "write_stdin" in name.lower()
        for name in tool_names_for_call(call["name"], call["input"])
    ):
        return []
    raw = call["input"]
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        parsed = None
    if isinstance(parsed, dict) and isinstance(parsed.get("chars"), str):
        return [parsed["chars"]]
    result: list[str] = []
    for match in re.finditer(
        r'(?:["\']chars["\']|\bchars)\s*:\s*("(?:\\.|[^"\\])*")', raw
    ):
        try:
            chars = json.loads(match.group(1))
        except json.JSONDecodeError:
            continue
        if isinstance(chars, str):
            result.append(chars)
    return result


def requests_termination(call: dict[str, str]) -> bool:
    names = [name.lower() for name in tool_names_for_call(call["name"], call["input"])]
    if not any(
        name.rsplit("__", 1)[-1].rsplit(".", 1)[-1] in {"wait", "write_stdin"}
        for name in names
    ):
        return False
    return bool(
        re.search(
            r'(?:["\']terminate["\']|\bterminate)\s*:\s*true',
            call["input"],
            re.IGNORECASE,
        )
    )


def contains_process_kill(value: str, depth: int = 0) -> bool:
    if depth > 3:
        return False
    for segment in shell_segments(value):
        try:
            words = shlex.split(segment, posix=True)
        except ValueError:
            continue
        while words:
            while words and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", words[0]):
                words.pop(0)
            if not words:
                break
            wrapper = words[0].rsplit("/", 1)[-1].lower()
            if wrapper not in {"sudo", "env", "command", "builtin"}:
                break
            words.pop(0)
            while words and words[0].startswith("-"):
                raw_option = words.pop(0)
                option = raw_option.split("=", 1)[0]
                if (
                    option
                    in {
                        "-u",
                        "--user",
                        "-g",
                        "--group",
                        "-h",
                        "--host",
                        "-p",
                        "--prompt",
                        "-C",
                        "--chdir",
                    }
                    and words
                    and "=" not in raw_option
                ):
                    words.pop(0)
        if not words:
            continue
        executable = words[0].rsplit("/", 1)[-1].lower()
        if executable in {"bash", "sh", "zsh"}:
            for index, word in enumerate(words[1:], 1):
                if (
                    word in {"-c", "-lc"}
                    and index + 1 < len(words)
                    and contains_process_kill(words[index + 1], depth + 1)
                ):
                    return True
        if executable in {"powershell", "powershell.exe", "pwsh", "pwsh.exe"}:
            for index, word in enumerate(words[1:], 1):
                if (
                    word.lower() in {"-command", "-c"}
                    and index + 1 < len(words)
                    and contains_process_kill(" ".join(words[index + 1 :]), depth + 1)
                ):
                    return True
        if executable in {"cmd", "cmd.exe"}:
            for index, word in enumerate(words[1:], 1):
                if (
                    word.lower() in {"/c", "-c"}
                    and index + 1 < len(words)
                    and contains_process_kill(" ".join(words[index + 1 :]), depth + 1)
                ):
                    return True
        if executable in {
            "pkill",
            "killall",
            "taskkill",
            "taskkill.exe",
            "stop-process",
        }:
            return True
        if executable == "kill" and len(words) > 1:
            if words[1] == "-0":
                continue
            if (
                len(words) > 2
                and words[1].lower() in {"-s", "-n", "--signal"}
                and words[2] == "0"
            ):
                continue
            if words[1].lower() == "--signal=0":
                continue
            return True
    return False


def shell_segments(value: str) -> list[str]:
    result: list[str] = []
    current: list[str] = []
    quote = ""
    index = 0
    while index < len(value):
        character = value[index]
        if quote:
            current.append(character)
            if character == quote and (index == 0 or value[index - 1] != "\\"):
                quote = ""
            index += 1
            continue
        if character in {"'", '"'}:
            quote = character
            current.append(character)
            index += 1
            continue
        separator_length = 0
        if value.startswith(("&&", "||"), index):
            separator_length = 2
        elif character in {";", "\n", "|", "&"}:
            separator_length = 1
        if separator_length:
            if segment := "".join(current).strip():
                result.append(segment)
            current.clear()
            index += separator_length
            continue
        current.append(character)
        index += 1
    if segment := "".join(current).strip():
        result.append(segment)
    return result


def audit_codex_session(
    rows: list[dict[str, Any]],
    metadata: dict[str, Any],
    had_prior_human: bool = False,
    usage_by_turn: dict[str, Counter[str]] | None = None,
) -> SessionAudit:
    started_day = (
        str(
            next((row.get("timestamp") for row in rows if row.get("timestamp")), "")
            or metadata.get("timestamp")
            or ""
        )[:10]
        or "unknown"
    )
    timeline: dict[str, Counter[str]] = defaultdict(Counter)
    timeline[started_day]["sessions"] = 1
    turn_models: dict[str, str] = {}
    model_counts: Counter[str] = Counter()
    inferred_turns = turn_ids_by_row(rows)
    for row, inferred_turn in zip(rows, inferred_turns, strict=True):
        if row.get("type") != "turn_context":
            continue
        payload = row.get("payload", {})
        model = safe_model_label(payload.get("model"))
        turn_id = row_turn_id(row, inferred_turn)
        if turn_id:
            turn_models[turn_id] = model
        model_counts[model] += 1
    dominant_model = model_counts.most_common(1)[0][0] if model_counts else "unknown"

    user_messages: list[dict[str, str]] = []
    seen_messages: set[tuple[str, str]] = set()
    for row_index, row in enumerate(rows):
        if row.get("type") != "response_item":
            continue
        payload = row.get("payload", {})
        if payload.get("type") != "message" or payload.get("role") != "user":
            continue
        text = clean_user_text(text_from_content(payload.get("content")))
        if not text:
            continue
        turn_id = row_turn_id(row, inferred_turns[row_index]) or str(
            payload.get("id") or f"row-{row_index}"
        )
        key = (turn_id, re.sub(r"\s+", " ", text))
        if key in seen_messages:
            continue
        seen_messages.add(key)
        user_messages.append(
            {
                "text": text,
                "model": turn_models.get(turn_id, dominant_model),
                "day": str(row.get("timestamp") or "")[:10] or started_day,
            }
        )

    corrections: list[dict[str, Any]] = []
    manual_acceptance = 0
    message_models: Counter[str] = Counter()
    for index, message in enumerate(user_messages):
        message_models[message["model"]] += 1
        timeline[message["day"]]["messages"] += 1
        if (
            (index or had_prior_human)
            and CORRECTION_GATE.search(message["text"])
            and CORRECTION_DIRECTED_RE.search(message["text"])
        ):
            categories = [
                name
                for name, pattern in CORRECTION_PATTERNS.items()
                if pattern.search(message["text"])
            ] or ["other_correction"]
            corrections.append(
                {
                    "categories": categories,
                    "model": message["model"],
                    "day": message["day"],
                    "excerpt": "Correction signal: " + ", ".join(categories),
                }
            )
            timeline[message["day"]]["corrections"] += 1
        if MANUAL_ACCEPTANCE_RE.search(message["text"]):
            manual_acceptance += 1

    calls: dict[str, dict[str, str]] = {}
    outputs: list[tuple[str, str, str]] = []
    tool_categories: Counter[str] = Counter()
    for row in rows:
        if row.get("type") != "response_item":
            continue
        payload = row.get("payload", {})
        item_type = payload.get("type")
        if item_type in {"custom_tool_call", "function_call"}:
            call_id = str(payload.get("call_id") or payload.get("id") or "")
            name = str(payload.get("name") or "unknown")
            raw_input = payload.get("input") or payload.get("arguments") or ""
            if not isinstance(raw_input, str):
                raw_input = json.dumps(raw_input, sort_keys=True)
            calls[call_id] = {"name": name, "input": raw_input}
            tool_categories.update(tool_categories_for_call(name, raw_input))
        elif item_type in {"custom_tool_call_output", "function_call_output"}:
            output = payload.get("output", "")
            if not isinstance(output, str):
                output = json.dumps(output, sort_keys=True)
            outputs.append(
                (
                    str(payload.get("call_id") or ""),
                    output,
                    str(row.get("timestamp") or "")[:10] or started_day,
                )
            )

    shell_call_ids = {
        call_id
        for call_id, call in calls.items()
        if "shell" in tool_categories_for_call(call["name"], call["input"])
    }
    commands_by_call = {
        call_id: shell_commands(call)
        for call_id, call in calls.items()
        if call_id in shell_call_ids
    }
    originating_commands = [
        command for commands in commands_by_call.values() for command in commands
    ]
    commands_by_session: dict[str, list[str]] = {}
    commands_by_cell: dict[str, list[str]] = {}
    deferred_call_ids: set[str] = set()
    for call_id, output, _day in outputs:
        session_id = session_id_from_output(output)
        if session_id and commands_by_call.get(call_id):
            commands_by_session[session_id] = commands_by_call[call_id]
            deferred_call_ids.add(call_id)
        cell_id = cell_id_from_output(output)
        if cell_id and commands_by_call.get(call_id):
            commands_by_cell[cell_id] = commands_by_call[call_id]
            deferred_call_ids.add(call_id)
    for call_id, call in calls.items():
        if not any(
            "write_stdin" in name.lower()
            for name in tool_names_for_call(call["name"], call["input"])
        ):
            continue
        session_id = session_id_from_input(call["input"])
        if session_id and session_id in commands_by_session:
            commands_by_call[call_id] = commands_by_session[session_id]
    for call_id, call in calls.items():
        if not any(
            name.lower().rsplit("__", 1)[-1].rsplit(".", 1)[-1] == "wait"
            for name in tool_names_for_call(call["name"], call["input"])
        ):
            continue
        cell_id = cell_id_from_input(call["input"])
        if cell_id and cell_id in commands_by_cell:
            commands_by_call[call_id] = commands_by_cell[cell_id]
    shell_outputs: list[tuple[str, str, str]] = []
    uncovered_shell_call_ids: set[str] = set()
    for call_id, output, day in outputs:
        if call_id in deferred_call_ids:
            continue
        commands = commands_by_call.get(call_id, [])
        envelopes = structured_result_envelopes(output)
        shell_invocation_count = sum(
            tool_category(name, "") == "shell"
            for name in tool_names_for_call(
                calls.get(call_id, {}).get("name", ""),
                calls.get(call_id, {}).get("input", ""),
            )
        )
        if len(commands) == 1 and shell_invocation_count == 1:
            shell_outputs.append(
                (commands[0], envelopes[0] if len(envelopes) == 1 else output, day)
            )
            continue
        if commands and len(envelopes) == len(commands):
            shell_outputs.extend(
                (command, envelope, day)
                for command, envelope in zip(commands, envelopes, strict=True)
            )
        elif call_id in shell_call_ids:
            uncovered_shell_call_ids.add(call_id)
    batched_shell_wrappers_uncovered = len(uncovered_shell_call_ids)
    shell_failures = 0
    shell_categories: Counter[str] = Counter()
    for command, output, day in shell_outputs:
        exit_code = structured_exit_code(output)
        if exit_code is None or exit_code == 0:
            continue
        shell_failures += 1
        category = shell_failure_category(command, output)
        shell_categories[category] += 1
        if category == "invocation_error":
            timeline[day]["shell_invocation_errors"] += 1

    command_inputs = originating_commands
    read_inputs = command_inputs + [
        call["input"]
        for call in calls.values()
        if re.search(r"view_image|read_file", call["name"], re.IGNORECASE)
        or (
            "visual_ui" in tool_categories_for_call(call["name"], call["input"])
            and "view_image" in call["input"]
        )
    ]
    terminate_inputs = [
        call["input"] for call in calls.values() if requests_termination(call)
    ]
    write_inputs = [
        chars for call in calls.values() for chars in write_stdin_chars(call) if chars
    ]
    process_kills = (
        sum(contains_process_kill(value) for value in command_inputs)
        + len(terminate_inputs)
        + sum("\x03" in value or contains_process_kill(value) for value in write_inputs)
    )
    normalized_read_inputs = [
        value.replace("\\\\", "/").replace("\\", "/") for value in read_inputs
    ]
    normalized_command_inputs = [
        value.replace("\\\\", "/").replace("\\", "/") for value in command_inputs
    ]
    personal_folder_reads = sum(
        bool(
            re.search(
                r"(?:/(?:Users|home)/[^/]+|~|\$(?:HOME|USERPROFILE)|"
                r"%(?:HOME|USERPROFILE)%)/(?:Desktop|Downloads|Documents|Library)"
                r"(?:/|\b)",
                value,
                re.IGNORECASE,
            )
        )
        for value in normalized_read_inputs
    )
    agent_history_reads = sum(
        bool(
            re.search(
                r"/\.(?:claude/projects|codex/(?:sessions|archived_sessions))(?:/|\b)",
                value,
                re.IGNORECASE,
            )
        )
        for value in normalized_command_inputs
    ) + sum(
        "read_thread" in name.lower()
        for call in calls.values()
        for name in tool_names_for_call(call["name"], call["input"])
    )
    test_calls = sum(
        bool(TEST_BUILD_COMMAND_RE.search(value)) for value in command_inputs
    )

    durations: list[int] = []
    automation_durations: list[int] = []
    current_turn = ""
    current_turn_started = ""
    turn_usage = cumulative_turn_usage(rows) if usage_by_turn is None else usage_by_turn
    substantive_usage: Counter[str] = Counter()
    automation_usage: Counter[str] = Counter()
    substantive_turns = 0
    automation_turns = 0
    turn_days: dict[str, str] = {}
    automation_turn_ids: set[str] = set()
    for row, inferred_turn in zip(rows, inferred_turns, strict=True):
        if row.get("type") != "response_item":
            continue
        payload = row.get("payload", {})
        if payload.get("type") != "message" or payload.get("role") != "user":
            continue
        raw_text = text_from_content(payload.get("content"))
        effective_text = clean_user_text(raw_text)
        automation_marker = re.search(
            r"<(?:heartbeat|automation)\b", raw_text, re.IGNORECASE
        )
        if not automation_marker or effective_text:
            continue
        turn_id = row_turn_id(row, inferred_turn)
        if turn_id:
            automation_turn_ids.add(turn_id)

    def finalize_turn(turn_id: str, duration: int = 0) -> None:
        nonlocal substantive_turns, automation_turns
        if not turn_id:
            return
        if turn_id in automation_turn_ids:
            automation_turns += 1
            if duration:
                automation_durations.append(duration)
            automation_usage.update(turn_usage.get(turn_id, {}))
            timeline[turn_days.get(turn_id, started_day)]["automation_turns"] += 1
        else:
            substantive_turns += 1
            if duration:
                durations.append(duration)
            substantive_usage.update(turn_usage.get(turn_id, {}))

    for row in rows:
        if row.get("type") != "event_msg":
            continue
        payload = row.get("payload", {})
        if payload.get("type") == "task_started":
            finalize_turn(current_turn)
            current_turn = row_turn_id(row)
            current_turn_started = str(row.get("timestamp") or "")
            turn_days[current_turn] = (
                str(row.get("timestamp") or "")[:10] or started_day
            )
        elif payload.get("type") == "task_complete":
            turn_id = row_turn_id(row, current_turn)
            duration = int(payload.get("duration_ms") or 0) or elapsed_milliseconds(
                current_turn_started, str(row.get("timestamp") or "")
            )
            finalize_turn(turn_id, duration)
            current_turn = ""
            current_turn_started = ""
    finalize_turn(current_turn)

    return SessionAudit(
        started_day=started_day,
        dominant_model=dominant_model,
        human_messages=len(user_messages),
        message_models=message_models,
        corrections=corrections,
        manual_acceptance=manual_acceptance,
        tool_categories=tool_categories,
        tool_calls=sum(
            len(tool_names_for_call(call["name"], call["input"]))
            for call in calls.values()
        ),
        shell_outputs=len(shell_outputs),
        shell_failures=shell_failures,
        shell_failure_categories=shell_categories,
        batched_shell_wrappers_uncovered=batched_shell_wrappers_uncovered,
        process_kills=process_kills,
        personal_folder_reads=personal_folder_reads,
        agent_history_reads=agent_history_reads,
        test_calls=test_calls,
        substantive_durations_ms=durations,
        automation_durations_ms=automation_durations,
        substantive_usage=substantive_usage,
        automation_usage=automation_usage,
        substantive_turns=substantive_turns,
        automation_turns=automation_turns,
        timeline=dict(timeline),
    )


def percentile(values: list[int], fraction: float) -> int:
    if not values:
        return 0
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, round((len(ordered) - 1) * fraction))]


def aggregate(sessions: list[SessionAudit], max_excerpts: int) -> dict[str, Any]:
    corrections = [item for session in sessions for item in session.corrections]
    messages = sum(session.human_messages for session in sessions)
    shell_outputs = sum(session.shell_outputs for session in sessions)
    shell_failures = sum(session.shell_failures for session in sessions)
    durations = [
        value for session in sessions for value in session.substantive_durations_ms
    ]
    automation_durations = [
        value for session in sessions for value in session.automation_durations_ms
    ]
    correction_categories: Counter[str] = Counter(
        category for correction in corrections for category in correction["categories"]
    )
    shell_categories: Counter[str] = Counter()
    tool_categories: Counter[str] = Counter()
    substantive_usage: Counter[str] = Counter()
    automation_usage: Counter[str] = Counter()
    per_model: dict[str, Counter[str]] = defaultdict(Counter)
    timeline: dict[str, Counter[str]] = defaultdict(Counter)
    for session in sessions:
        shell_categories.update(session.shell_failure_categories)
        tool_categories.update(session.tool_categories)
        substantive_usage.update(session.substantive_usage)
        automation_usage.update(session.automation_usage)
        correction_models = Counter(item["model"] for item in session.corrections)
        for model, message_count in session.message_models.items():
            per_model[model].update(
                sessions=1,
                messages=message_count,
                corrections=correction_models[model],
            )
        for day, values in session.timeline.items():
            timeline[day].update(values)
    token_total = substantive_usage["total_tokens"] + automation_usage["total_tokens"]
    invocation_errors = shell_categories["invocation_error"]
    metrics = {
        "sessions": len(sessions),
        "human_messages": messages,
        "correction_messages": len(corrections),
        "corrections_per_100_messages": round(100 * len(corrections) / messages, 2)
        if messages
        else 0,
        "manual_acceptance_requests": sum(
            session.manual_acceptance for session in sessions
        ),
        "tool_calls": sum(session.tool_calls for session in sessions),
        "shell_tool_outputs": shell_outputs,
        "shell_tool_failures": shell_failures,
        "batched_shell_wrappers_uncovered": sum(
            session.batched_shell_wrappers_uncovered for session in sessions
        ),
        "shell_tool_failure_rate_percent": round(
            100 * shell_failures / shell_outputs, 2
        )
        if shell_outputs
        else 0,
        "shell_invocation_errors": invocation_errors,
        "shell_invocation_errors_per_100_tool_outputs": round(
            100 * invocation_errors / shell_outputs, 2
        )
        if shell_outputs
        else 0,
        "process_kill_calls": sum(session.process_kills for session in sessions),
        "personal_folder_read_calls": sum(
            session.personal_folder_reads for session in sessions
        ),
        "agent_history_read_calls": sum(
            session.agent_history_reads for session in sessions
        ),
        "test_or_review_calls": sum(session.test_calls for session in sessions),
        "substantive_turns": sum(session.substantive_turns for session in sessions),
        "automation_turns": sum(session.automation_turns for session in sessions),
        "automation_token_share_percent": round(
            100 * automation_usage["total_tokens"] / token_total, 2
        )
        if token_total
        else 0,
    }
    model_data = {}
    for model, values in sorted(per_model.items()):
        model_data[model] = dict(values)
        model_data[model]["corrections_per_100_messages"] = (
            round(100 * values["corrections"] / values["messages"], 2)
            if values["messages"]
            else 0
        )
    return {
        "metrics": metrics,
        "correction_categories": dict(correction_categories.most_common()),
        "shell_failure_categories": dict(shell_categories.most_common()),
        "tool_categories": dict(tool_categories.most_common()),
        "duration_ms": {
            "median": int(statistics.median(durations)) if durations else 0,
            "p90": percentile(durations, 0.90),
            "max": max(durations, default=0),
            "automation_median": int(statistics.median(automation_durations))
            if automation_durations
            else 0,
        },
        "token_usage": {
            "substantive": dict(substantive_usage),
            "automation": dict(automation_usage),
        },
        "per_model": model_data,
        "timeline": {day: dict(values) for day, values in sorted(timeline.items())},
        "correction_excerpts": corrections[:max_excerpts],
    }


def claude_counts(
    root: Path, scope: RepositoryScope, since: date | None, until: date | None
) -> dict[str, int]:
    direct_sessions = 0
    human_messages = 0
    if not root.is_dir():
        return {"direct_sessions": 0, "human_messages": 0}
    for path in root.glob("*/*.jsonl"):
        rows = load_jsonl(path)
        cwd_metadata = next(
            ({"cwd": row.get("cwd")} for row in rows if row.get("cwd")), {}
        )
        if not matches_repository(cwd_metadata, scope):
            continue
        audit_workflow_active = False
        session_messages: list[str] = []
        for row in rows:
            if row.get("type") != "user":
                continue
            text = clean_user_text(
                text_from_content((row.get("message") or {}).get("content"))
            )
            if not text:
                continue
            if AUDIT_SESSION_RE.search(text):
                audit_workflow_active = True
                continue
            if audit_workflow_active and (
                AUDIT_FOLLOWUP_RE.search(text)
                or (AUDIT_FEEDBACK_RE.search(text) and CORRECTION_GATE.search(text))
            ):
                continue
            audit_workflow_active = False
            timestamp = str(row.get("timestamp") or "")
            if timestamp and in_window(timestamp, since, until):
                session_messages.append(text)
        if not session_messages:
            continue
        direct_sessions += 1
        human_messages += len(session_messages)
    return {"direct_sessions": direct_sessions, "human_messages": human_messages}


def load_case_notes(path: Path | None) -> list[dict[str, str]]:
    if path is None:
        return []
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise AuditError(f"cannot read causal notes: {error}") from error
    if not isinstance(raw, list):
        raise AuditError("causal notes must be a JSON array")
    notes = []
    for index, item in enumerate(raw):
        if not isinstance(item, dict):
            raise AuditError(f"causal note {index + 1} must be an object")
        missing = {
            key for key in ("title", "cause", "control", "status") if not item.get(key)
        }
        if missing:
            raise AuditError(
                f"causal note {index + 1} missing: {', '.join(sorted(missing))}"
            )
        notes.append(
            {
                key: redact(str(item[key]), 320)
                for key in ("title", "cause", "control", "status")
            }
        )
    return notes


def window_days(window: dict[str, Any]) -> int | None:
    since = parse_day(window.get("since"), "baseline --since")
    until = parse_day(window.get("until"), "baseline --until")
    if since is None or until is None:
        return None
    if since > until:
        raise AuditError("baseline window starts after it ends")
    return (until - since).days + 1


def build_comparison(
    current: dict[str, Any], current_scope: dict[str, Any], baseline_path: Path | None
) -> dict[str, Any] | None:
    if baseline_path is None:
        return None
    try:
        baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise AuditError(f"cannot read baseline: {error}") from error
    if baseline.get("schema_version") != SCHEMA_VERSION or not isinstance(
        baseline.get("metrics"), dict
    ):
        raise AuditError("baseline was not produced by this audit schema")
    baseline_scope = baseline.get("scope")
    if not isinstance(baseline_scope, dict):
        raise AuditError("baseline is missing its audit scope")
    if not baseline_scope.get("repository_identity") or (
        baseline_scope.get("repository_identity")
        != current_scope.get("repository_identity")
    ):
        raise AuditError(
            "baseline repository identity does not match the current repository"
        )
    baseline_window = baseline_scope.get("window")
    current_window = current_scope.get("window")
    if not isinstance(baseline_window, dict) or not isinstance(current_window, dict):
        raise AuditError("baseline or current audit is missing its window")
    baseline_days = window_days(baseline_window)
    current_days = window_days(current_window)
    if baseline_days is None or current_days is None:
        if baseline_window != current_window:
            raise AuditError(
                "open-ended baseline and current windows must match exactly"
            )
    elif baseline_days != current_days:
        raise AuditError(
            "baseline and current audit windows must span the same number of days"
        )
    metrics = {}
    for key in COMPARISON_KEYS:
        before = baseline["metrics"].get(key, 0)
        after = current.get(key, 0)
        metrics[key] = {
            "baseline": before,
            "current": after,
            "delta": round(after - before, 2),
        }
    return {
        "baseline_generated_at": baseline.get("generated_at", "unknown"),
        "baseline_window": baseline.get("scope", {}).get("window", {}),
        "metrics": metrics,
    }


def validate_privacy(value: Any) -> None:
    text = json.dumps(value, ensure_ascii=False)
    raw_strings: list[str] = []

    allowed_host_labels: set[str] = set()
    if isinstance(value, dict):
        scope = value.get("scope")
        if isinstance(scope, dict) and isinstance(scope.get("repository"), str):
            allowed_host_labels.add(scope["repository"])

    def collect_strings(item: Any) -> None:
        if isinstance(item, str):
            raw_strings.append(item)
        elif isinstance(item, dict):
            for key, nested in item.items():
                collect_strings(key)
                collect_strings(nested)
        elif isinstance(item, (list, tuple)):
            for nested in item:
                collect_strings(nested)

    collect_strings(value)
    if any(HOME_PATH_RE.search(raw) for raw in raw_strings):
        raise AuditError("privacy check rejected a home-relative filesystem path")
    if any(ABSOLUTE_PATH_RE.search(raw) for raw in raw_strings):
        raise AuditError("privacy check rejected an absolute filesystem path")
    if any(RELATIVE_PATH_RE.search(raw) for raw in raw_strings):
        raise AuditError("privacy check rejected a relative filesystem path")
    if any(EMAIL_RE.search(raw) for raw in raw_strings):
        raise AuditError("privacy check rejected an email-shaped value")
    if any(PRIVATE_IP_RE.search(raw) for raw in raw_strings):
        raise AuditError("privacy check rejected a private IP address")
    forbidden = (
        r"file://",
        r"\b[A-Za-z][A-Za-z0-9+.-]*://",
        r"\.codex/(?:sessions|archived_sessions)",
        r"\.claude/projects",
        r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b",
    )
    for pattern in forbidden:
        if re.search(pattern, text, re.IGNORECASE):
            raise AuditError(
                f"privacy check rejected generated content matching {pattern!r}"
            )
    if any(
        HOSTNAME_RE.search(raw) for raw in raw_strings if raw not in allowed_host_labels
    ):
        raise AuditError("privacy check rejected a hostname-shaped value")
    if any(pattern.search(raw) for pattern in SECRET_PATTERNS for raw in raw_strings):
        raise AuditError("privacy check rejected a credential-shaped value")
    if any(LABELED_ID_RE.search(raw) for raw in raw_strings):
        raise AuditError("privacy check rejected a labeled runtime identifier")


def validate_html_privacy(html_text: str, repository_label: str = "") -> None:
    visible_html = re.sub(
        r"<(?:style|script)\b[^>]*>.*?</(?:style|script)>",
        " ",
        html_text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    text_only = re.sub(r"<[^>]+>", " ", visible_html)
    text_only = html.unescape(text_only)
    value: Any = text_only
    if repository_label:
        value = {
            "scope": {"repository": repository_label},
            "rendered_text": text_only.replace(repository_label, "[repository]"),
        }
    validate_privacy(value)
    if re.search(r"\b(?:src|href)\s*=", html_text, re.IGNORECASE):
        raise AuditError("privacy check rejected an HTML external-resource attribute")


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, delete=False
    ) as handle:
        handle.write(content)
        temporary = Path(handle.name)
    temporary.replace(path)


def format_number(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:,.2f}".rstrip("0").rstrip(".")
    if isinstance(value, int):
        return f"{value:,}"
    return str(value)


def render_bars(title: str, values: dict[str, Any]) -> str:
    maximum = max((float(value) for value in values.values()), default=1) or 1
    rows = []
    for name, value in values.items():
        width = max(2, round(100 * float(value) / maximum))
        rows.append(
            f'<div class="bar"><span>{html.escape(name.replace("_", " "))}</span>'
            f'<i><b style="width:{width}%"></b></i><strong>{format_number(value)}</strong></div>'
        )
    return f'<section><h2>{html.escape(title)}</h2><div class="panel">{"".join(rows) or "No data"}</div></section>'


def render_html(dataset: dict[str, Any]) -> str:
    metrics = dataset["metrics"]
    scope = dataset["scope"]
    cards = [
        ("Sessions", metrics["sessions"]),
        ("Human messages", metrics["human_messages"]),
        ("Corrections / 100", metrics["corrections_per_100_messages"]),
        ("Shell invocation errors", metrics["shell_invocation_errors"]),
        ("Automation token share", f"{metrics['automation_token_share_percent']}%"),
        ("History-read calls", metrics["agent_history_read_calls"]),
        ("Claude direct sessions", scope["claude_direct_sessions"]),
        ("Claude human messages", scope["claude_human_messages"]),
    ]
    card_html = "".join(
        f'<div class="card"><span>{html.escape(label)}</span><strong>{format_number(value)}</strong></div>'
        for label, value in cards
    )
    comparison = dataset.get("comparison")
    comparison_html = ""
    if comparison:
        rows = []
        for key, values in comparison["metrics"].items():
            delta = values["delta"]
            delta_text = (
                f"+{format_number(delta)}" if delta > 0 else format_number(delta)
            )
            rows.append(
                f'<div class="compare"><span>{html.escape(key.replace("_", " "))}</span>'
                f"<span>{format_number(values['baseline'])}</span>"
                f"<span>{format_number(values['current'])}</span><strong>{delta_text}</strong></div>"
            )
        comparison_html = (
            '<section><h2>Change from baseline</h2><div class="panel">'
            '<div class="compare head"><span>Metric</span><span>Before</span><span>Now</span><span>Delta</span></div>'
            + "".join(rows)
            + "</div></section>"
        )
    excerpts = "".join(
        "<li><span>"
        + html.escape(", ".join(item["categories"]))
        + "</span><p>"
        + html.escape(item["excerpt"])
        + "</p></li>"
        for item in dataset["correction_excerpts"]
    )
    notes = "".join(
        "<article><div><strong>"
        + html.escape(note["title"])
        + "</strong><small>"
        + html.escape(note["status"])
        + "</small></div><p><b>Cause:</b> "
        + html.escape(note["cause"])
        + "</p><p><b>Control:</b> "
        + html.escape(note["control"])
        + "</p></article>"
        for note in dataset["causal_case_notes"]
    )
    window = scope["window"]
    window_text = f"{window.get('since') or 'first record'} to {window.get('until') or 'latest record'}"
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(scope["repository"])} Codex performance audit</title>
<style>
:root{{--bg:#000;--panel:#111;--line:#2b2b2b;--text:#fff;--muted:#aaa;--accent:#74e0b8;--warn:#ffce67}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--text);font:15px/1.5 system-ui,sans-serif}}
main{{width:min(1100px,calc(100% - 32px));margin:auto;padding:48px 0 72px}}h1{{font-size:clamp(30px,6vw,58px);line-height:1.02;margin:0 0 16px;max-width:900px}}
h2{{font-size:22px;margin:40px 0 12px}}p{{color:var(--muted)}}.intro{{font-size:18px;max-width:780px}}.grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-top:28px}}
.card,.panel,article{{background:var(--panel);border:1px solid var(--line);border-radius:10px}}.card{{padding:18px}}.card span,.card strong{{display:block}}.card span{{color:var(--muted)}}.card strong{{font-size:29px;margin-top:8px}}
.panel{{padding:8px 16px}}.bar{{display:grid;grid-template-columns:190px 1fr 70px;gap:14px;align-items:center;padding:9px 0;border-bottom:1px solid var(--line)}}.bar:last-child{{border:0}}.bar span{{color:var(--muted)}}.bar i{{height:8px;background:#222;border-radius:9px;overflow:hidden}}.bar b{{display:block;height:100%;background:var(--accent)}}
.compare{{display:grid;grid-template-columns:2fr repeat(3,1fr);gap:10px;padding:9px 0;border-bottom:1px solid var(--line)}}.compare:last-child{{border:0}}.compare span:first-child{{color:var(--muted)}}.compare.head{{font-size:12px;text-transform:uppercase;color:var(--muted)}}
ul{{list-style:none;padding:0;margin:0}}li{{border-top:1px solid var(--line);padding:14px 0}}li span,small{{color:var(--accent);font-size:12px;text-transform:uppercase;letter-spacing:.04em}}li p{{margin:5px 0 0;color:var(--text)}}article{{padding:17px;margin:10px 0}}article div{{display:flex;justify-content:space-between;gap:16px}}article p{{margin:8px 0 0}}article b{{color:var(--text)}}
.method{{border-left:3px solid var(--warn);padding-left:16px;max-width:850px}}code{{color:var(--accent)}}
@media(max-width:720px){{.grid{{grid-template-columns:1fr 1fr}}.bar{{grid-template-columns:120px 1fr 55px}}.compare{{grid-template-columns:1.6fr repeat(3,1fr);font-size:12px}}}}
@media(max-width:480px){{.grid{{grid-template-columns:1fr}}main{{width:min(100% - 22px,1100px);padding-top:30px}}}}
</style></head><body><main>
<header><h1>{html.escape(scope["repository"])} Codex performance audit</h1><p class="intro">Behavioral signals from local Codex histories, with separate Claude activity coverage counts. Window: {html.escape(window_text)}. Generated {html.escape(dataset["generated_at"][:19])}.</p></header>
<div class="grid">{card_html}</div>
{comparison_html}
{render_bars("Correction categories", dataset["correction_categories"])}
{render_bars("Shell failure taxonomy", dataset["shell_failure_categories"])}
{render_bars("Tool categories", dataset["tool_categories"])}
<section><h2>Correction signal samples</h2><div class="panel"><ul>{excerpts or "<li>No correction signals in this window.</li>"}</ul></div></section>
<section><h2>Causal cases</h2>{notes or '<div class="panel"><p>No causal notes supplied for this run.</p></div>'}</section>
<section><h2>Method and limits</h2><div class="method"><p>{html.escape(scope["privacy"])}</p><p>Correction detection favors precision. Shell nonzero results include intentional tests and probes. Token totals are model-accounted usage, not billing. Compare only reports from this schema with matching scope.</p></div></section>
</main></body></html>"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate privacy-minimized JSON and HTML from local Codex histories.",
        epilog=(
            "Example:\n"
            "  audit_agent_history.py --repo /path/to/repo --marker repo-name "
            "--since 2026-08-01 --output-dir /path/to/visualization"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")
    parser.add_argument(
        "--repo",
        type=Path,
        required=True,
        help="repository used to label and validate scope",
    )
    parser.add_argument(
        "--marker",
        action="append",
        default=[],
        help="exact lowercase target repository basename; repeatable",
    )
    parser.add_argument("--since", help="inclusive start date, YYYY-MM-DD")
    parser.add_argument("--until", help="inclusive end date, YYYY-MM-DD")
    parser.add_argument(
        "--output-dir", type=Path, help="destination outside the product repository"
    )
    parser.add_argument("--baseline", type=Path, help="prior JSON from this script")
    parser.add_argument(
        "--case-notes", type=Path, help="privacy-reviewed causal notes JSON"
    )
    parser.add_argument(
        "--exclude-session",
        action="append",
        default=[],
        help="session ID to exclude; repeatable",
    )
    parser.add_argument(
        "--max-excerpts",
        type=int,
        default=12,
        help="maximum redacted corrections (default: 12)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="print machine-readable result paths and metrics",
    )
    return parser


def configured_state_root(variable: str, default_name: str) -> Path:
    configured = os.environ.get(variable, "").strip()
    return (
        Path(configured).expanduser().resolve()
        if configured
        else Path.home() / default_name
    )


def run(args: argparse.Namespace) -> tuple[dict[str, Any], Path, Path]:
    repo = args.repo.expanduser().resolve()
    if not repo.is_dir():
        raise AuditError(f"repository does not exist: {repo}")
    if args.max_excerpts < 0 or args.max_excerpts > 50:
        raise AuditError("--max-excerpts must be between 0 and 50")
    since = parse_day(args.since, "--since")
    until = parse_day(args.until, "--until")
    if since and until and since > until:
        raise AuditError("--since must not be after --until")
    markers = [value.strip().lower() for value in args.marker if value.strip()]
    if not markers:
        markers = [repo.name.lower()]
    scope_identity = repository_scope(repo, markers)
    codex_home = configured_state_root("CODEX_HOME", ".codex")
    claude_home = configured_state_root("CLAUDE_CONFIG_DIR", ".claude")
    output_dir = (
        args.output_dir.expanduser().resolve()
        if args.output_dir
        else codex_home / "visualizations" / "agent-performance-audit" / repo.name
    )
    validate_artifact_paths(repo, output_dir, args.baseline, args.case_notes)
    explicit_exclusions = set(args.exclude_session)
    codex_roots = [
        codex_home / "sessions",
        codex_home / "archived_sessions",
    ]
    all_codex = deduplicated_codex_files(codex_roots)
    selected: list[SessionAudit] = []
    audit_exclusions = 0
    matched_explicit_exclusions: set[str] = set()
    for path in all_codex:
        metadata = first_metadata(path)
        session_id = str(metadata.get("session_id") or metadata.get("id") or path.stem)
        if not matches_repository(metadata, scope_identity):
            continue
        rows = load_jsonl(path)
        all_turn_usage = cumulative_turn_usage(rows)
        excluded_audit_turns = audit_turn_ids(rows)
        if session_id in explicit_exclusions:
            matched_explicit_exclusions.add(session_id)
            if not excluded_audit_turns:
                raise AuditError(
                    "--exclude-session matched a repository session without a "
                    "detectable audit turn; refusing to drop substantive history"
                )
        if audit_turns_in_window(rows, excluded_audit_turns, since, until):
            audit_exclusions += 1
        windowed_rows = codex_turns_in_window(
            rows, since, until, excluded_turns=excluded_audit_turns
        )
        if not windowed_rows:
            continue
        selected.append(
            audit_codex_session(
                windowed_rows,
                metadata,
                had_prior_human=has_prior_human_message(
                    rows, windowed_rows, excluded_audit_turns
                ),
                usage_by_turn={
                    turn_id: usage
                    for turn_id, usage in all_turn_usage.items()
                    if turn_id not in excluded_audit_turns
                },
            )
        )
    validate_explicit_exclusions(explicit_exclusions, matched_explicit_exclusions)

    aggregate_data = aggregate(selected, args.max_excerpts)
    claude = claude_counts(claude_home / "projects", scope_identity, since, until)
    generated_at = datetime.now().astimezone().isoformat()
    dataset = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at,
        "scope": {
            "repository": repo.name,
            "repository_identity": scope_identity.identity,
            "window": {"since": args.since, "until": args.until},
            "codex_histories_scanned": len(all_codex),
            "codex_sessions_in_scope": len(selected),
            "claude_direct_sessions": claude["direct_sessions"],
            "claude_human_messages": claude["human_messages"],
            "excluded_audit_sessions": audit_exclusions,
            "privacy": (
                "Artifacts contain aggregate metrics, tool categories, duration summaries, category-only "
                "correction signals, and supplied causal notes only. Raw histories remain local."
            ),
        },
        **aggregate_data,
        "causal_case_notes": load_case_notes(args.case_notes),
    }
    dataset["comparison"] = build_comparison(
        dataset["metrics"], dataset["scope"], args.baseline
    )
    validate_privacy(dataset)
    json_text = json.dumps(dataset, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    html_text = render_html(dataset)
    validate_html_privacy(html_text, repo.name)
    if len(html_text.encode("utf-8")) > MAX_HTML_BYTES:
        raise AuditError("generated HTML exceeds 512 KB")
    json_path = output_dir / "agent-performance-audit.json"
    html_path = output_dir / "agent-performance-audit.html"
    atomic_write(json_path, json_text)
    atomic_write(html_path, html_text)
    return dataset, json_path, html_path


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        dataset, json_path, html_path = run(args)
    except AuditError as error:
        print(f"audit-agent-performance: {error}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("audit-agent-performance: interrupted", file=sys.stderr)
        return 130
    result = {
        "json": str(json_path),
        "html": str(html_path),
        "metrics": dataset["metrics"],
    }
    if args.json:
        print(json.dumps(result, sort_keys=True))
    else:
        print(f"JSON: {json_path}")
        print(f"HTML: {html_path}")
        print(
            "Summary: "
            f"{dataset['metrics']['sessions']} sessions, "
            f"{dataset['metrics']['corrections_per_100_messages']} corrections/100 messages, "
            f"{dataset['metrics']['shell_invocation_errors']} invocation errors, "
            f"{dataset['metrics']['automation_token_share_percent']}% automation tokens"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
