#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPT = Path(__file__).with_name("audit_agent_history.py")
SPEC = importlib.util.spec_from_file_location("audit_agent_history", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
AUDIT = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = AUDIT
SPEC.loader.exec_module(AUDIT)


class AuditPrivacyTests(unittest.TestCase):
    def test_configured_state_root_honors_profile_environment(self) -> None:
        with (
            tempfile.TemporaryDirectory() as directory,
            mock.patch.dict(
                "os.environ",
                {"CODEX_HOME": directory, "CLAUDE_CONFIG_DIR": directory},
                clear=True,
            ),
        ):
            self.assertEqual(
                AUDIT.configured_state_root("CODEX_HOME", ".codex"),
                Path(directory).resolve(),
            )
            self.assertEqual(
                AUDIT.configured_state_root("CLAUDE_CONFIG_DIR", ".claude"),
                Path(directory).resolve(),
            )

    def test_redact_removes_sensitive_shapes(self) -> None:
        value = AUDIT.redact(
            "See /Users/person/private.txt https://private.example/a "
            "person@example.com 019ff27c-8084-7853-b5a8-51be8d7d2eae"
        )
        self.assertNotIn("/Users/", value)
        self.assertNotIn("https://", value)
        self.assertNotIn("person@example.com", value)
        self.assertNotIn("019ff27c", value)

    def test_redact_local_domain_email(self) -> None:
        for email in ("alice@corp", "alice@localhost", "alice@例子.测试"):
            value = AUDIT.redact(f"Contact {email}")
            self.assertNotIn(email, value)
            self.assertIn("[email]", value)
            with self.assertRaises(AUDIT.AuditError):
                AUDIT.validate_privacy({"value": email})

    def test_redact_all_absolute_paths(self) -> None:
        for path in (
            "/tmp/private-project/file.txt",
            "/Volumes/client work/scene.ma",
            "C:\\work\\private\\scene.ma",
            "cwd:/Users/person/private-project",
            "/客户/project/scene.ma",
        ):
            value = AUDIT.redact(f"Open {path} before review")
            self.assertNotIn(path, value)
            self.assertIn("[path]", value)
            with self.assertRaises(AUDIT.AuditError):
                AUDIT.validate_privacy({"path": path})

    def test_redact_relative_paths(self) -> None:
        for path in (
            "clients/acme/scene.ma",
            "src/private_feature.py",
            "clients\\acme\\scene.ma",
            "\\\\server\\share\\private\\scene.ma",
            "client/secrets",
            "../private",
            "a/private.py",
            "src/x",
            "客户/project.txt",
        ):
            value = AUDIT.redact(f"Inspect {path} before review")
            self.assertNotIn(path, value)
            self.assertIn("[path]", value)
            with self.assertRaises(AUDIT.AuditError):
                AUDIT.validate_privacy({"path": path})

    def test_json_escaped_newline_is_not_a_relative_path(self) -> None:
        AUDIT.validate_privacy({"value": "first line\nsecond line"})

    def test_redact_home_paths(self) -> None:
        for path in ("~/.ssh/id_rsa", "$HOME/Documents/client", "%USERPROFILE%/secret"):
            value = AUDIT.redact(f"Inspect {path}")
            self.assertNotIn(path, value)
            self.assertIn("[path]", value)
            with self.assertRaises(AUDIT.AuditError):
                AUDIT.validate_privacy({"path": path})

    def test_redact_private_uris(self) -> None:
        for uri in (
            "ssh://internal-host/repository",
            "smb://server/share",
            "ftp://private-host/data",
        ):
            value = AUDIT.redact(f"Open {uri}")
            self.assertNotIn(uri, value)
            self.assertIn("[url]", value)
            with self.assertRaises(AUDIT.AuditError):
                AUDIT.validate_privacy({"uri": uri})

    def test_redact_removes_realistic_github_token_prefixes(self) -> None:
        for token in (
            "ghp_" + "a" * 32,
            "github_pat_" + "b" * 40,
        ):
            value = AUDIT.redact(f"token={token}")
            self.assertNotIn(token, value)
            self.assertIn("[secret]", value)
            with self.assertRaises(AUDIT.AuditError):
                AUDIT.validate_privacy({"token": token})

    def test_redact_unlabelled_google_api_key(self) -> None:
        token = "AIza" + "a" * 35
        value = AUDIT.redact(f"Observed {token}")
        self.assertNotIn(token, value)
        self.assertIn("[secret]", value)
        with self.assertRaises(AUDIT.AuditError):
            AUDIT.validate_privacy({"value": token})

    def test_common_credentials(self) -> None:
        values = (
            "AKIA" + "A" * 16,
            "eyJ" + "a" * 12 + "." + "b" * 12 + "." + "c" * 12,
            "Bearer " + "d" * 24,
            "Author" + "ization: Ba" + "sic " + "Z" * 24,
            "password=" + "e" * 16,
            "AWS_SECRET_ACCESS_KEY=" + "f" * 24,
            "DATABASE_URL=" + "postgres" + "://" + "user:pass@example.invalid/db",
            "glpat-" + "g" * 24,
            "npm_" + "h" * 24,
            "SECRET_KEY=" + "i" * 24,
            "sk_live_" + "j" * 24,
            "rk_" + "li" + "ve_" + "k" * 24,
            'password="correct horse battery staple"',
            "password=correct horse battery staple",
        )
        for secret in values:
            value = AUDIT.redact(f"Observed {secret}")
            self.assertNotIn(secret, value)
            self.assertRegex(value, r"\[(?:secret|url)\]")
            with self.assertRaises(AUDIT.AuditError):
                AUDIT.validate_privacy({"value": secret})
        multiword = AUDIT.redact("password=correct horse battery staple")
        for word in ("correct", "horse", "battery", "staple"):
            self.assertNotIn(word, multiword)

    def test_natural_language_credential_label(self) -> None:
        secret = "test_value_" + "x" * 20
        value = AUDIT.redact(f"The API key is {secret} and it still doesn't work")
        self.assertNotIn(secret, value)
        self.assertIn("[secret]", value)
        with self.assertRaises(AUDIT.AuditError):
            AUDIT.validate_privacy({"value": f"The API key is {secret}"})

    def test_short_natural_language_credential(self) -> None:
        secret = "hunter2"
        value = AUDIT.redact(f"The password is {secret} and it still doesn't work")
        self.assertNotIn(secret, value)
        self.assertIn("[secret]", value)
        with self.assertRaises(AUDIT.AuditError):
            AUDIT.validate_privacy({"value": f"The password is {secret}"})

    def test_very_short_explicit_credentials(self) -> None:
        for secret in (
            'password="abc12"',
            "pin=1234",
            "passcode=7",
            '{"password":"hunter2"}',
            '{"token":"abc123"}',
            "password hunter2",
            "API key: abc123",
            "secret key abc123",
        ):
            value = AUDIT.redact(f"Wrong: {secret}")
            self.assertNotIn(secret, value)
            self.assertIn("[secret]", value)
            with self.assertRaises(AUDIT.AuditError):
                AUDIT.validate_privacy({"value": secret})

    def test_scheme_less_private_hostname(self) -> None:
        host = "www.private.example"
        value = AUDIT.redact(f"{host} is still broken")
        self.assertNotIn(host, value)
        self.assertIn("[host]", value)
        with self.assertRaises(AUDIT.AuditError):
            AUDIT.validate_privacy({"value": host})

    def test_private_ip_endpoint(self) -> None:
        endpoint = "192.168.1.25:8080"
        value = AUDIT.redact(f"{endpoint} is still broken")
        self.assertNotIn(endpoint, value)
        self.assertIn("[private-ip]", value)
        with self.assertRaises(AUDIT.AuditError):
            AUDIT.validate_privacy({"value": endpoint})

    def test_dotted_repository_label_is_allowed(self) -> None:
        AUDIT.validate_privacy(
            {
                "scope": {"repository": "three.js"},
                "metrics": {"sessions": 1},
            }
        )
        AUDIT.validate_html_privacy(
            "<html><body>three.js audit</body></html>", "three.js"
        )

    def test_html_privacy_ignores_markup_but_checks_text(self) -> None:
        AUDIT.validate_html_privacy("<html><body>Safe report</body></html>")
        AUDIT.validate_html_privacy(
            "<html><style>.compare.head{color:red}</style><body>Safe</body></html>"
        )
        with self.assertRaises(AUDIT.AuditError):
            AUDIT.validate_html_privacy(
                "<html><body>/Users/person/private</body></html>"
            )
        with self.assertRaises(AUDIT.AuditError):
            AUDIT.validate_html_privacy(
                '<html><a href="https://example.invalid">x</a></html>'
            )

    def test_private_key_material(self) -> None:
        key = (
            "-----BEGIN " + "OPENSSH PRIVATE KEY-----\n" + "a" * 48 + "\n"
            "-----END " + "OPENSSH PRIVATE KEY-----"
        )
        value = AUDIT.redact(f"Observed {key}")
        self.assertNotIn("PRIVATE KEY", value)
        self.assertIn("[secret]", value)
        with self.assertRaises(AUDIT.AuditError):
            AUDIT.validate_privacy({"value": key})

    def test_labeled_runtime_ids(self) -> None:
        for labeled_id in (
            "session_id=42",
            "session ID abc123",
            "thread_id:thread-7",
            "host ID maya01",
            '"session_id":"42"',
            '"thread_id": "worker-7"',
            'session ID "abc"',
        ):
            value = AUDIT.redact(f"Observed {labeled_id}")
            self.assertNotIn(labeled_id, value)
            self.assertIn("[id]", value)
            with self.assertRaises(AUDIT.AuditError):
                AUDIT.validate_privacy({"value": labeled_id})

    def test_clean_user_text_keeps_only_ambient_request(self) -> None:
        raw = "<in-app-browser-context>private</in-app-browser-context>\n## My request:\nFix this"
        self.assertEqual(AUDIT.clean_user_text(raw), "Fix this")

    def test_mixed_injected_and_human_content_keeps_human_text(self) -> None:
        raw = "<system-reminder>state</system-reminder>\nFix this"
        self.assertEqual(AUDIT.clean_user_text(raw), "Fix this")
        raw = (
            '<in-app-browser-context source="state">private</in-app-browser-context>\n'
            "Fix login"
        )
        self.assertEqual(AUDIT.clean_user_text(raw), "Fix login")

    def test_tool_mention_is_not_audit(self) -> None:
        rows = [
            {
                "type": "response_item",
                "payload": {
                    "type": "custom_tool_call",
                    "input": "read audit_agent_history.py",
                },
            }
        ]
        self.assertFalse(AUDIT.session_is_audit(rows))

    def test_maintenance_request_is_not_audit(self) -> None:
        rows = [
            {
                "type": "response_item",
                "payload": {
                    "type": "message",
                    "role": "user",
                    "turn_id": "maintenance",
                    "content": [
                        {
                            "type": "input_text",
                            "text": "Fix token accounting in audit_agent_history.py",
                        }
                    ],
                },
            }
        ]
        self.assertEqual(AUDIT.audit_turn_ids(rows), set())

    def test_run_tests_for_audit_script_is_not_audit(self) -> None:
        rows = [
            {
                "type": "response_item",
                "payload": {
                    "type": "message",
                    "role": "user",
                    "turn_id": "maintenance",
                    "content": [
                        {
                            "type": "input_text",
                            "text": "Run tests for audit_agent_history.py",
                        }
                    ],
                },
            }
        ]
        self.assertEqual(AUDIT.audit_turn_ids(rows), set())

    def test_audit_script_cli_is_audit(self) -> None:
        rows = [
            {
                "type": "response_item",
                "payload": {
                    "type": "message",
                    "role": "user",
                    "turn_id": "audit",
                    "content": [
                        {
                            "type": "input_text",
                            "text": "python audit_agent_history.py --repo project",
                        }
                    ],
                },
            }
        ]
        self.assertEqual(AUDIT.audit_turn_ids(rows), {"audit"})

    def test_default_skill_prompt_is_audit(self) -> None:
        rows = [
            {
                "type": "response_item",
                "payload": {
                    "type": "message",
                    "role": "user",
                    "turn_id": "audit",
                    "content": [
                        {
                            "type": "input_text",
                            "text": "Use $agent-performance-audit to compare recent performance",
                        }
                    ],
                },
            }
        ]
        self.assertEqual(AUDIT.audit_turn_ids(rows), {"audit"})

    def test_natural_audit_request_and_followup(self) -> None:
        rows = [
            {
                "type": "response_item",
                "payload": {
                    "type": "message",
                    "role": "user",
                    "turn_id": "audit",
                    "content": [
                        {
                            "type": "input_text",
                            "text": "Audit agent performance for this repository",
                        }
                    ],
                },
            },
            {
                "type": "response_item",
                "payload": {
                    "type": "message",
                    "role": "user",
                    "turn_id": "followup",
                    "content": [
                        {"type": "input_text", "text": "Rerun audit with baseline"}
                    ],
                },
            },
            {
                "type": "response_item",
                "payload": {
                    "type": "message",
                    "role": "user",
                    "turn_id": "maintenance",
                    "content": [{"type": "input_text", "text": "Fix this parser"}],
                },
            },
        ]
        self.assertEqual(AUDIT.audit_turn_ids(rows), {"audit", "followup"})

    def test_polite_audit_followup(self) -> None:
        rows = [
            {
                "type": "response_item",
                "payload": {
                    "type": "message",
                    "role": "user",
                    "turn_id": "audit",
                    "content": [
                        {"type": "input_text", "text": "Audit agent performance"}
                    ],
                },
            },
            {
                "type": "response_item",
                "payload": {
                    "type": "message",
                    "role": "user",
                    "turn_id": "followup",
                    "content": [
                        {
                            "type": "input_text",
                            "text": "Please rerun the audit with the baseline",
                        }
                    ],
                },
            },
        ]
        self.assertEqual(AUDIT.audit_turn_ids(rows), {"audit", "followup"})

    def test_audit_message_uses_active_task_when_turn_id_is_missing(self) -> None:
        rows = [
            {
                "type": "event_msg",
                "payload": {"type": "task_started", "turn_id": "audit"},
            },
            {
                "type": "response_item",
                "payload": {
                    "type": "message",
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": "Audit agent performance"}
                    ],
                },
            },
            {
                "type": "event_msg",
                "payload": {"type": "task_complete", "turn_id": "audit"},
            },
        ]
        self.assertEqual(AUDIT.audit_turn_ids(rows), {"audit"})

    def test_audit_message_uses_following_task_when_turn_id_is_missing(self) -> None:
        rows = [
            {
                "type": "response_item",
                "payload": {
                    "type": "message",
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": "Audit agent performance"}
                    ],
                },
            },
            {
                "type": "event_msg",
                "payload": {"type": "task_started", "turn_id": "audit"},
            },
            {
                "type": "event_msg",
                "payload": {"type": "task_complete", "turn_id": "audit"},
            },
        ]
        self.assertEqual(AUDIT.audit_turn_ids(rows), {"audit"})

    def test_audit_correction_remains_excluded(self) -> None:
        rows = [
            {
                "type": "response_item",
                "payload": {
                    "type": "message",
                    "role": "user",
                    "turn_id": "audit",
                    "content": [
                        {"type": "input_text", "text": "Audit agent performance"}
                    ],
                },
            },
            {
                "type": "response_item",
                "payload": {
                    "type": "message",
                    "role": "user",
                    "turn_id": "feedback",
                    "content": [
                        {
                            "type": "input_text",
                            "text": "This report is wrong; fix the missing sessions",
                        }
                    ],
                },
            },
        ]
        self.assertEqual(AUDIT.audit_turn_ids(rows), {"audit", "feedback"})

    def test_unrelated_correction_starts_new_work(self) -> None:
        rows = [
            {
                "type": "response_item",
                "payload": {
                    "type": "message",
                    "role": "user",
                    "turn_id": "audit",
                    "content": [
                        {"type": "input_text", "text": "Audit agent performance"}
                    ],
                },
            },
            {
                "type": "response_item",
                "payload": {
                    "type": "message",
                    "role": "user",
                    "turn_id": "work",
                    "content": [
                        {
                            "type": "input_text",
                            "text": "Fix the login; it is still broken",
                        }
                    ],
                },
            },
        ]
        self.assertEqual(AUDIT.audit_turn_ids(rows), {"audit"})

    def test_unrelated_session_work_starts_new_work(self) -> None:
        rows = [
            {
                "type": "response_item",
                "payload": {
                    "type": "message",
                    "role": "user",
                    "turn_id": "audit",
                    "content": [
                        {"type": "input_text", "text": "Audit agent performance"}
                    ],
                },
            },
            {
                "type": "response_item",
                "payload": {
                    "type": "message",
                    "role": "user",
                    "turn_id": "work",
                    "content": [
                        {"type": "input_text", "text": "Fix the login session timeout"}
                    ],
                },
            },
        ]
        self.assertEqual(AUDIT.audit_turn_ids(rows), {"audit"})

    def test_unrelated_report_work_starts_new_work(self) -> None:
        rows = [
            {
                "type": "response_item",
                "payload": {
                    "type": "message",
                    "role": "user",
                    "turn_id": "audit",
                    "content": [
                        {"type": "input_text", "text": "Audit agent performance"}
                    ],
                },
            },
            {
                "type": "response_item",
                "payload": {
                    "type": "message",
                    "role": "user",
                    "turn_id": "work",
                    "content": [
                        {"type": "input_text", "text": "Fix the customer report export"}
                    ],
                },
            },
        ]
        self.assertEqual(AUDIT.audit_turn_ids(rows), {"audit"})

    def test_unrelated_metric_work_starts_new_work(self) -> None:
        for text in (
            "Add a metric for exporter latency",
            "Include this finding in the product report",
        ):
            rows = [
                {
                    "type": "response_item",
                    "payload": {
                        "type": "message",
                        "role": "user",
                        "turn_id": "audit",
                        "content": [
                            {"type": "input_text", "text": "Audit agent performance"}
                        ],
                    },
                },
                {
                    "type": "response_item",
                    "payload": {
                        "type": "message",
                        "role": "user",
                        "turn_id": "work",
                        "content": [{"type": "input_text", "text": text}],
                    },
                },
            ]
            self.assertEqual(AUDIT.audit_turn_ids(rows), {"audit"})

    def test_short_audit_continuation_remains_excluded(self) -> None:
        for followup in ("Include July too", "Add the previous baseline"):
            rows = [
                {
                    "type": "response_item",
                    "payload": {
                        "type": "message",
                        "role": "user",
                        "turn_id": "audit",
                        "content": [
                            {"type": "input_text", "text": "Audit agent performance"}
                        ],
                    },
                },
                {
                    "type": "response_item",
                    "payload": {
                        "type": "message",
                        "role": "user",
                        "turn_id": "followup",
                        "content": [{"type": "input_text", "text": followup}],
                    },
                },
            ]
            self.assertEqual(AUDIT.audit_turn_ids(rows), {"audit", "followup"})

    def test_advertised_audit_triggers(self) -> None:
        for text in (
            "Run the monthly agent-performance check",
            "Do a post-issue-batch workflow review",
            "Do a Theo-style agent audit for this repository",
        ):
            rows = [
                {
                    "type": "response_item",
                    "payload": {
                        "type": "message",
                        "role": "user",
                        "turn_id": "audit",
                        "content": [{"type": "input_text", "text": text}],
                    },
                }
            ]
            self.assertEqual(AUDIT.audit_turn_ids(rows), {"audit"})

    def test_injected_message_keeps_audit_workflow(self) -> None:
        rows = [
            {
                "type": "response_item",
                "payload": {
                    "type": "message",
                    "role": "user",
                    "turn_id": "audit",
                    "content": [
                        {"type": "input_text", "text": "Audit agent performance"}
                    ],
                },
            },
            {
                "type": "response_item",
                "payload": {
                    "type": "message",
                    "role": "user",
                    "turn_id": "injected",
                    "content": [
                        {"type": "input_text", "text": "<heartbeat>state</heartbeat>"}
                    ],
                },
            },
            {
                "type": "response_item",
                "payload": {
                    "type": "message",
                    "role": "user",
                    "turn_id": "followup",
                    "content": [
                        {"type": "input_text", "text": "Rerun audit with baseline"}
                    ],
                },
            },
        ]
        self.assertEqual(AUDIT.audit_turn_ids(rows), {"audit", "followup"})

    def test_generic_continuation_is_not_audit(self) -> None:
        rows = [
            {
                "type": "response_item",
                "payload": {
                    "type": "message",
                    "role": "user",
                    "turn_id": "audit",
                    "content": [
                        {"type": "input_text", "text": "Audit agent performance"}
                    ],
                },
            },
            {
                "type": "response_item",
                "payload": {
                    "type": "message",
                    "role": "user",
                    "turn_id": "work",
                    "content": [
                        {
                            "type": "input_text",
                            "text": "Continue implementing issue 123",
                        }
                    ],
                },
            },
        ]
        self.assertEqual(AUDIT.audit_turn_ids(rows), {"audit"})

    def test_exclude_only_audit_turn(self) -> None:
        rows = [
            {
                "timestamp": "2026-08-01T00:00:00Z",
                "type": "event_msg",
                "payload": {"type": "task_started", "turn_id": "normal"},
            },
            {
                "timestamp": "2026-08-01T00:01:00Z",
                "type": "event_msg",
                "payload": {"type": "task_complete", "turn_id": "normal"},
            },
            {
                "timestamp": "2026-08-01T00:02:00Z",
                "type": "event_msg",
                "payload": {"type": "task_started", "turn_id": "audit"},
            },
            {
                "timestamp": "2026-08-01T00:02:01Z",
                "type": "response_item",
                "payload": {
                    "type": "message",
                    "role": "user",
                    "turn_id": "audit",
                    "content": [
                        {"type": "input_text", "text": "Run agent-performance-audit"}
                    ],
                },
            },
            {
                "timestamp": "2026-08-01T00:03:00Z",
                "type": "event_msg",
                "payload": {"type": "task_complete", "turn_id": "audit"},
            },
        ]
        excluded = AUDIT.audit_turn_ids(rows)
        selected = AUDIT.codex_turns_in_window(
            rows,
            AUDIT.date(2026, 8, 1),
            AUDIT.date(2026, 8, 1),
            excluded_turns=excluded,
        )
        self.assertEqual(excluded, {"audit"})
        self.assertEqual({row["payload"]["turn_id"] for row in selected}, {"normal"})

    def test_audit_exclusion_count_respects_window(self) -> None:
        rows = [
            {
                "timestamp": "2026-07-01T00:00:00Z",
                "type": "event_msg",
                "payload": {"type": "task_started", "turn_id": "old-audit"},
            },
            {
                "timestamp": "2026-08-01T00:00:00Z",
                "type": "event_msg",
                "payload": {"type": "task_started", "turn_id": "current"},
            },
        ]
        selected = AUDIT.audit_turns_in_window(
            rows,
            {"old-audit"},
            AUDIT.date(2026, 8, 1),
            AUDIT.date(2026, 8, 31),
        )
        self.assertEqual(selected, set())

    def test_unmatched_explicit_exclusion_is_rejected(self) -> None:
        with self.assertRaises(AUDIT.AuditError):
            AUDIT.validate_explicit_exclusions({"missing"}, set())

    def test_artifact_paths_reject_repo_output_and_baseline_overwrite(self) -> None:
        repo = Path("/project/repo")
        with self.assertRaises(AUDIT.AuditError):
            AUDIT.validate_artifact_paths(repo, repo / "reports", None, None)
        output = Path("/reports")
        for filename in (
            "agent-performance-audit.json",
            "agent-performance-audit.html",
        ):
            artifact = output / filename
            with self.assertRaises(AUDIT.AuditError):
                AUDIT.validate_artifact_paths(repo, output, artifact, None)
            with self.assertRaises(AUDIT.AuditError):
                AUDIT.validate_artifact_paths(repo, output, None, artifact)

    def test_token_snapshots_use_cumulative_delta(self) -> None:
        rows = [
            {
                "type": "event_msg",
                "payload": {
                    "type": "token_count",
                    "info": {"total_token_usage": {"total_tokens": 100}},
                },
            },
            {"type": "event_msg", "payload": {"type": "task_started", "turn_id": "t"}},
            {
                "type": "event_msg",
                "payload": {
                    "type": "token_count",
                    "info": {"total_token_usage": {"total_tokens": 110}},
                },
            },
            {
                "type": "event_msg",
                "payload": {
                    "type": "token_count",
                    "info": {"total_token_usage": {"total_tokens": 125}},
                },
            },
            {
                "type": "event_msg",
                "payload": {"type": "task_complete", "turn_id": "t", "duration_ms": 1},
            },
        ]
        result = AUDIT.audit_codex_session(rows, {"timestamp": "2026-08-12"})
        self.assertEqual(result.substantive_usage["total_tokens"], 25)
        self.assertEqual(result.substantive_turns, 1)

    def test_zero_duration_turn_is_counted(self) -> None:
        rows = [
            {"type": "event_msg", "payload": {"type": "task_started", "turn_id": "t"}},
            {"type": "event_msg", "payload": {"type": "task_complete", "turn_id": "t"}},
        ]
        result = AUDIT.audit_codex_session(rows, {"timestamp": "2026-08-12"})
        self.assertEqual(result.substantive_turns, 1)
        self.assertEqual(result.substantive_durations_ms, [])

    def test_duration_falls_back_to_task_timestamps(self) -> None:
        rows = [
            {
                "timestamp": "2026-08-12T10:00:00Z",
                "type": "event_msg",
                "payload": {"type": "task_started", "turn_id": "t"},
            },
            {
                "timestamp": "2026-08-12T10:00:02.500Z",
                "type": "event_msg",
                "payload": {"type": "task_complete", "turn_id": "t"},
            },
        ]
        result = AUDIT.audit_codex_session(rows, {"timestamp": "2026-08-12"})
        self.assertEqual(result.substantive_durations_ms, [2500])

    def test_incomplete_turn_is_counted(self) -> None:
        rows = [
            {"type": "event_msg", "payload": {"type": "task_started", "turn_id": "t"}},
            {
                "type": "event_msg",
                "payload": {
                    "type": "token_count",
                    "info": {"total_token_usage": {"total_tokens": 17}},
                },
            },
        ]
        result = AUDIT.audit_codex_session(rows, {"timestamp": "2026-08-12"})
        self.assertEqual(result.substantive_turns, 1)
        self.assertEqual(result.substantive_usage["total_tokens"], 17)

    def test_heartbeat_usage_is_classified_from_user_input(self) -> None:
        rows = [
            {"type": "event_msg", "payload": {"type": "task_started", "turn_id": "t"}},
            {
                "type": "response_item",
                "payload": {
                    "type": "message",
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": "<heartbeat>run</heartbeat>"}
                    ],
                    "internal_chat_message_metadata_passthrough": {"turn_id": "t"},
                },
            },
            {
                "type": "event_msg",
                "payload": {
                    "type": "token_count",
                    "info": {"total_token_usage": {"total_tokens": 15}},
                },
            },
            {
                "type": "event_msg",
                "payload": {
                    "type": "task_complete",
                    "turn_id": "t",
                    "duration_ms": 1,
                    "last_agent_message": "done",
                },
            },
        ]
        result = AUDIT.audit_codex_session(rows, {"timestamp": "2026-08-12"})
        self.assertEqual(result.automation_usage["total_tokens"], 15)
        self.assertFalse(result.substantive_usage)

    def test_heartbeat_after_injected_context_is_automation(self) -> None:
        rows = [
            {
                "type": "event_msg",
                "payload": {"type": "task_started", "turn_id": "t"},
            },
            {
                "type": "response_item",
                "payload": {
                    "type": "message",
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": (
                                "<environment_context>state</environment_context>\n"
                                "<heartbeat>run</heartbeat>"
                            ),
                        }
                    ],
                    "internal_chat_message_metadata_passthrough": {"turn_id": "t"},
                },
            },
            {
                "type": "event_msg",
                "payload": {
                    "type": "token_count",
                    "info": {"total_token_usage": {"total_tokens": 15}},
                },
            },
            {
                "type": "event_msg",
                "payload": {"type": "task_complete", "turn_id": "t"},
            },
        ]
        result = AUDIT.audit_codex_session(rows, {"timestamp": "2026-08-12"})
        self.assertEqual(result.automation_turns, 1)
        self.assertEqual(result.automation_usage["total_tokens"], 15)

    def test_untagged_heartbeat_before_task_start_is_automation(self) -> None:
        rows = [
            {
                "type": "response_item",
                "payload": {
                    "type": "message",
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": "<heartbeat>run</heartbeat>"}
                    ],
                },
            },
            {"type": "event_msg", "payload": {"type": "task_started", "turn_id": "t"}},
            {
                "type": "event_msg",
                "payload": {
                    "type": "token_count",
                    "info": {"total_token_usage": {"total_tokens": 15}},
                },
            },
            {
                "type": "event_msg",
                "payload": {"type": "task_complete", "turn_id": "t"},
            },
        ]
        result = AUDIT.audit_codex_session(rows, {"timestamp": "2026-08-12"})
        self.assertEqual(result.automation_turns, 1)
        self.assertEqual(result.automation_usage["total_tokens"], 15)
        self.assertEqual(result.substantive_turns, 0)

    def test_untagged_user_message_uses_inferred_turn_model(self) -> None:
        rows = [
            {
                "type": "response_item",
                "payload": {
                    "type": "message",
                    "role": "user",
                    "content": [{"type": "input_text", "text": "Fix this"}],
                },
            },
            {"type": "event_msg", "payload": {"type": "task_started", "turn_id": "t"}},
            {
                "type": "turn_context",
                "payload": {"turn_id": "t", "model": "target-model"},
            },
            {
                "type": "turn_context",
                "payload": {"turn_id": "other", "model": "other-model"},
            },
        ]
        result = AUDIT.audit_codex_session(rows, {"timestamp": "2026-08-12"})
        self.assertEqual(result.message_models, {"target-model": 1})

    def test_untagged_turn_context_uses_inferred_turn(self) -> None:
        rows = [
            {
                "type": "event_msg",
                "payload": {"type": "task_started", "turn_id": "target"},
            },
            {
                "type": "turn_context",
                "payload": {"model": "target-model"},
            },
            {
                "type": "response_item",
                "payload": {
                    "type": "message",
                    "role": "user",
                    "content": [{"type": "input_text", "text": "Work"}],
                },
            },
        ]
        result = AUDIT.audit_codex_session(rows, {"timestamp": "2026-08-12"})
        self.assertEqual(result.message_models, {"target-model": 1})

    def test_date_window(self) -> None:
        rows = [
            {"timestamp": "2026-07-31T23:59:59Z", "value": "before"},
            {"timestamp": "2026-08-01T00:00:00Z", "value": "inside"},
            {"timestamp": "2026-09-01T00:00:00Z", "value": "after"},
        ]
        selected = AUDIT.rows_in_date_window(
            rows, AUDIT.date(2026, 8, 1), AUDIT.date(2026, 8, 31)
        )
        self.assertEqual([row["value"] for row in selected], ["inside"])

    def test_complete_turn_window(self) -> None:
        rows = [
            {
                "timestamp": "2026-07-31T23:59:59Z",
                "type": "event_msg",
                "payload": {"type": "task_started", "turn_id": "before"},
            },
            {
                "timestamp": "2026-08-01T00:00:00Z",
                "type": "event_msg",
                "payload": {"type": "task_complete", "turn_id": "before"},
            },
            {
                "timestamp": "2026-08-31T23:59:59Z",
                "type": "event_msg",
                "payload": {"type": "task_started", "turn_id": "inside"},
            },
            {
                "timestamp": "2026-09-01T00:00:00Z",
                "type": "event_msg",
                "payload": {"type": "task_complete", "turn_id": "inside"},
            },
        ]
        selected = AUDIT.codex_turns_in_window(
            rows, AUDIT.date(2026, 8, 1), AUDIT.date(2026, 8, 31)
        )
        self.assertEqual(
            [row["payload"]["turn_id"] for row in selected], ["inside", "inside"]
        )

    def test_untagged_user_before_task_start_is_included(self) -> None:
        rows = [
            {
                "timestamp": "2026-08-01T00:00:00Z",
                "type": "response_item",
                "payload": {
                    "type": "message",
                    "role": "user",
                    "content": [{"type": "input_text", "text": "Fix this"}],
                },
            },
            {
                "timestamp": "2026-08-01T00:00:01Z",
                "type": "event_msg",
                "payload": {"type": "task_started", "turn_id": "inside"},
            },
            {
                "timestamp": "2026-08-01T00:01:00Z",
                "type": "event_msg",
                "payload": {"type": "task_complete", "turn_id": "inside"},
            },
        ]
        selected = AUDIT.codex_turns_in_window(
            rows, AUDIT.date(2026, 8, 1), AUDIT.date(2026, 8, 1)
        )
        self.assertEqual(selected, rows)

    def test_repository_identity_ignores_branch(self) -> None:
        scope = AUDIT.RepositoryScope(
            Path("/projects/target"),
            "example.invalid/target",
            frozenset({"target"}),
        )
        metadata = {
            "cwd": "/projects/other",
            "git": {
                "repository_url": "https://example.invalid/other.git",
                "branch": "feature/target",
            },
        }
        self.assertFalse(AUDIT.matches_repository(metadata, scope))
        metadata["git"]["repository_url"] = "https://example.invalid/target.git"
        self.assertTrue(AUDIT.matches_repository(metadata, scope))

    def test_repository_scope_rejects_conflicting_remote_at_same_path(self) -> None:
        scope = AUDIT.RepositoryScope(
            Path("/projects/target"),
            "example.invalid/target",
            frozenset({"target"}),
        )
        metadata = {
            "cwd": "/projects/target",
            "git": {"repository_url": "https://example.invalid/fork.git"},
        }
        self.assertFalse(AUDIT.matches_repository(metadata, scope))

    def test_repository_scope_rejects_non_git_directory(self) -> None:
        with (
            tempfile.TemporaryDirectory() as directory,
            self.assertRaises(AUDIT.AuditError),
        ):
            AUDIT.repository_scope(Path(directory), [])

    def test_history_discovery_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            later = root / "z" / "session.jsonl"
            earlier = root / "a" / "session.jsonl"
            later.parent.mkdir()
            earlier.parent.mkdir()
            row = json.dumps({"payload": {"session_id": "same"}}) + "\n"
            later.write_text(row)
            earlier.write_text(row)
            selected = AUDIT.deduplicated_codex_files([root])
        self.assertEqual(selected, [earlier])

    def test_model_and_timeline_attribution(self) -> None:
        rows = [
            {
                "timestamp": "2026-08-01T12:00:00Z",
                "type": "turn_context",
                "payload": {"turn_id": "one", "model": "model-one"},
            },
            {
                "timestamp": "2026-08-01T12:01:00Z",
                "type": "response_item",
                "payload": {
                    "type": "message",
                    "role": "user",
                    "turn_id": "one",
                    "content": [{"type": "input_text", "text": "Start"}],
                },
            },
            {
                "timestamp": "2026-08-02T12:00:00Z",
                "type": "turn_context",
                "payload": {"turn_id": "two", "model": "model-two"},
            },
            {
                "timestamp": "2026-08-02T12:01:00Z",
                "type": "response_item",
                "payload": {
                    "type": "message",
                    "role": "user",
                    "turn_id": "two",
                    "content": [{"type": "input_text", "text": "Still broken"}],
                },
            },
        ]
        session = AUDIT.audit_codex_session(rows, {"timestamp": "2026-08-01"})
        result = AUDIT.aggregate([session], 10)
        self.assertEqual(result["per_model"]["model-one"]["messages"], 1)
        self.assertEqual(result["per_model"]["model-two"]["corrections"], 1)
        self.assertEqual(result["timeline"]["2026-08-02"]["corrections"], 1)

    def test_namespaced_model_is_privacy_safe(self) -> None:
        self.assertEqual(AUDIT.safe_model_label("openai/gpt-5"), "openai:gpt-5")
        AUDIT.validate_privacy(
            {"per_model": {AUDIT.safe_model_label("openai/gpt-5"): {"messages": 1}}}
        )

    def test_direct_claude_counts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            project = root / "project"
            nested = project / "session" / "subagents"
            nested.mkdir(parents=True)
            row = {
                "timestamp": "2026-08-12T12:00:00Z",
                "cwd": "/projects/target",
                "type": "user",
                "message": {"content": [{"type": "text", "text": "Work"}]},
            }
            (project / "direct.jsonl").write_text(json.dumps(row) + "\n")
            (nested / "agent.jsonl").write_text(json.dumps(row) + "\n")
            scope = AUDIT.RepositoryScope(
                Path("/projects/target"), "", frozenset({"target"})
            )
            counts = AUDIT.claude_counts(
                root, scope, AUDIT.date(2026, 8, 12), AUDIT.date(2026, 8, 12)
            )
        self.assertEqual(counts, {"direct_sessions": 1, "human_messages": 1})

    def test_claude_injected_message_filter(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            project = root / "project"
            project.mkdir()
            rows = [
                {
                    "timestamp": "2026-08-12T12:00:00Z",
                    "cwd": "/projects/target",
                    "type": "user",
                    "message": {
                        "content": [
                            {
                                "type": "text",
                                "text": "<system-reminder>state</system-reminder>",
                            }
                        ]
                    },
                }
            ]
            (project / "direct.jsonl").write_text(
                "".join(json.dumps(row) + "\n" for row in rows)
            )
            scope = AUDIT.RepositoryScope(
                Path("/projects/target"), "", frozenset({"target"})
            )
            counts = AUDIT.claude_counts(
                root, scope, AUDIT.date(2026, 8, 12), AUDIT.date(2026, 8, 12)
            )
        self.assertEqual(counts, {"direct_sessions": 0, "human_messages": 0})

    def test_claude_audit_session_is_excluded(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            project = root / "project"
            project.mkdir()
            row = {
                "timestamp": "2026-08-12T12:00:00Z",
                "cwd": "/projects/target",
                "type": "user",
                "message": {
                    "content": [{"type": "text", "text": "Audit agent performance"}]
                },
            }
            (project / "direct.jsonl").write_text(json.dumps(row) + "\n")
            scope = AUDIT.RepositoryScope(
                Path("/projects/target"), "", frozenset({"target"})
            )
            counts = AUDIT.claude_counts(
                root, scope, AUDIT.date(2026, 8, 12), AUDIT.date(2026, 8, 12)
            )
        self.assertEqual(counts, {"direct_sessions": 0, "human_messages": 0})

    def test_claude_mixed_session_keeps_normal_work(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            project = root / "project"
            project.mkdir()
            rows = [
                {
                    "timestamp": "2026-07-31T12:00:00Z",
                    "cwd": "/projects/target",
                    "type": "user",
                    "message": {
                        "content": [{"type": "text", "text": "Audit agent performance"}]
                    },
                },
                {
                    "timestamp": "2026-08-01T12:00:00Z",
                    "cwd": "/projects/target",
                    "type": "user",
                    "message": {
                        "content": [
                            {
                                "type": "text",
                                "text": "Please rerun the audit with the baseline",
                            }
                        ]
                    },
                },
                {
                    "timestamp": "2026-08-02T12:00:00Z",
                    "cwd": "/projects/target",
                    "type": "user",
                    "message": {"content": [{"type": "text", "text": "Fix feature"}]},
                },
            ]
            (project / "direct.jsonl").write_text(
                "".join(json.dumps(row) + "\n" for row in rows)
            )
            scope = AUDIT.RepositoryScope(
                Path("/projects/target"), "", frozenset({"target"})
            )
            counts = AUDIT.claude_counts(
                root, scope, AUDIT.date(2026, 8, 1), AUDIT.date(2026, 8, 31)
            )
        self.assertEqual(counts, {"direct_sessions": 1, "human_messages": 1})

    def test_indirect_process_kill(self) -> None:
        self.assertTrue(AUDIT.contains_process_kill('kill -TERM "$upload_pid"'))
        self.assertFalse(AUDIT.contains_process_kill('kill -0 "$upload_pid"'))
        self.assertFalse(AUDIT.contains_process_kill("kill -s 0 42"))
        self.assertFalse(AUDIT.contains_process_kill("kill -n 0 42"))
        self.assertFalse(AUDIT.contains_process_kill("rg 'pkill|kill -TERM' source.py"))
        self.assertFalse(
            AUDIT.contains_process_kill("rg '\"terminate\": true' source.py")
        )
        self.assertTrue(AUDIT.contains_process_kill("sudo pkill -TERM helper"))
        self.assertTrue(AUDIT.contains_process_kill("sudo --user=root kill -TERM 123"))
        self.assertTrue(AUDIT.contains_process_kill("env MODE=x kill -TERM 123"))
        self.assertTrue(AUDIT.contains_process_kill("/usr/bin/sudo kill -TERM 123"))
        self.assertTrue(
            AUDIT.contains_process_kill("env MODE=x sudo -u root kill -TERM 123")
        )
        self.assertTrue(AUDIT.contains_process_kill("bash -lc 'kill -TERM 42'"))
        self.assertTrue(
            AUDIT.contains_process_kill("bash -lc 'prepare && kill -TERM 42'")
        )
        self.assertTrue(AUDIT.contains_process_kill("sh -c 'cleanup; pkill helper'"))
        self.assertTrue(
            AUDIT.contains_process_kill("powershell -Command 'Stop-Process -Id 42'")
        )
        self.assertTrue(AUDIT.contains_process_kill("cmd /c taskkill /pid 42"))
        self.assertTrue(AUDIT.contains_process_kill("taskkill.exe /PID 42"))
        self.assertTrue(AUDIT.contains_process_kill("printf x | pkill helper"))
        self.assertTrue(AUDIT.contains_process_kill("prepare & kill -TERM 42"))

    def test_structured_history_read_and_pty_interrupt_metrics(self) -> None:
        rows = [
            {
                "type": "response_item",
                "payload": {
                    "type": "function_call",
                    "call_id": "read",
                    "name": "read_thread",
                    "arguments": "{}",
                },
            },
            {
                "type": "response_item",
                "payload": {
                    "type": "function_call",
                    "call_id": "stop",
                    "name": "write_stdin",
                    "arguments": '{"session_id":1,"chars":"\\u0003"}',
                },
            },
        ]
        result = AUDIT.audit_codex_session(rows, {"timestamp": "2026-08-12"})
        self.assertEqual(result.agent_history_reads, 1)
        self.assertEqual(result.process_kills, 1)

    def test_windows_personal_and_history_read_metrics(self) -> None:
        rows = [
            {
                "type": "response_item",
                "payload": {
                    "type": "function_call",
                    "call_id": "read",
                    "name": "exec_command",
                    "arguments": (
                        '{"cmd":"type C:\\\\\\\\Users\\\\\\\\person\\\\\\\\Documents\\\\\\\\note.txt '
                        'C:\\\\\\\\Users\\\\\\\\person\\\\\\\\.codex\\\\\\\\sessions\\\\\\\\one.jsonl"}'
                    ),
                },
            }
        ]
        result = AUDIT.audit_codex_session(rows, {"timestamp": "2026-08-12"})
        self.assertEqual(result.personal_folder_reads, 1)
        self.assertEqual(result.agent_history_reads, 1)

    def test_home_relative_personal_folder_read_metrics(self) -> None:
        for path in (
            "~/Documents/note.txt",
            "$HOME/Downloads/item.zip",
            "%USERPROFILE%/Documents/note.txt",
        ):
            rows = [
                {
                    "type": "response_item",
                    "payload": {
                        "type": "function_call",
                        "call_id": "read",
                        "name": "exec_command",
                        "arguments": json.dumps({"cmd": f"type {path}"}),
                    },
                }
            ]
            result = AUDIT.audit_codex_session(rows, {"timestamp": "2026-08-12"})
            self.assertEqual(result.personal_folder_reads, 1)

    def test_nested_history_read_and_pty_interrupt_metrics(self) -> None:
        rows = [
            {
                "type": "response_item",
                "payload": {
                    "type": "function_call",
                    "call_id": "wrapped",
                    "name": "functions.exec",
                    "arguments": (
                        "await tools.read_thread({}); "
                        'await tools.write_stdin({"session_id":1,"chars":"\\u0003"})'
                    ),
                },
            }
        ]
        result = AUDIT.audit_codex_session(rows, {"timestamp": "2026-08-12"})
        self.assertEqual(result.agent_history_reads, 1)
        self.assertEqual(result.process_kills, 1)

    def test_write_stdin_kill_and_wrapped_output_metrics(self) -> None:
        rows = [
            {
                "type": "response_item",
                "payload": {
                    "type": "function_call",
                    "call_id": "start",
                    "name": "exec_command",
                    "arguments": '{"cmd":"long-task"}',
                },
            },
            {
                "type": "response_item",
                "payload": {
                    "type": "function_call_output",
                    "call_id": "start",
                    "output": '{"session_id":7,"output":"running"}',
                },
            },
            {
                "type": "response_item",
                "payload": {
                    "type": "function_call",
                    "call_id": "continue",
                    "name": "functions.exec",
                    "arguments": (
                        'await tools.write_stdin({"session_id":7,'
                        '"chars":"kill -TERM 123\\n"})'
                    ),
                },
            },
            {
                "type": "response_item",
                "payload": {
                    "type": "function_call_output",
                    "call_id": "continue",
                    "output": '{"exit_code":1,"output":"failed"}',
                },
            },
        ]
        result = AUDIT.audit_codex_session(rows, {"timestamp": "2026-08-12"})
        self.assertEqual(result.process_kills, 1)
        self.assertEqual(result.shell_outputs, 1)
        self.assertEqual(result.shell_failures, 1)

    def test_batched_shell_result_envelopes_are_counted(self) -> None:
        rows = [
            {
                "type": "response_item",
                "payload": {
                    "type": "function_call",
                    "call_id": "batch",
                    "name": "functions.exec",
                    "arguments": (
                        'await tools.exec_command({"cmd":"first"}); '
                        'await tools.exec_command({"cmd":"second"})'
                    ),
                },
            },
            {
                "type": "response_item",
                "payload": {
                    "type": "function_call_output",
                    "call_id": "batch",
                    "output": json.dumps(
                        {
                            "results": [
                                {"exit_code": 0, "output": "ok"},
                                {"exit_code": 2, "output": "failed"},
                            ]
                        }
                    ),
                },
            },
        ]
        result = AUDIT.audit_codex_session(rows, {"timestamp": "2026-08-12"})
        self.assertEqual(result.shell_outputs, 2)
        self.assertEqual(result.shell_failures, 1)
        self.assertEqual(result.batched_shell_wrappers_uncovered, 0)

    def test_single_shell_uses_nested_result_envelope(self) -> None:
        rows = [
            {
                "type": "response_item",
                "payload": {
                    "type": "function_call",
                    "call_id": "wrapped",
                    "name": "functions.exec",
                    "arguments": (
                        'await tools.exec_command({"cmd":"one"}); '
                        'await tools.view_image({"path":"image.png"})'
                    ),
                },
            },
            {
                "type": "response_item",
                "payload": {
                    "type": "function_call_output",
                    "call_id": "wrapped",
                    "output": json.dumps(
                        {"results": [{"exit_code": 2, "output": "failed"}]}
                    ),
                },
            },
        ]
        result = AUDIT.audit_codex_session(rows, {"timestamp": "2026-08-12"})
        self.assertEqual(result.shell_outputs, 1)
        self.assertEqual(result.shell_failures, 1)

    def test_partially_parsed_shell_batch_is_uncovered(self) -> None:
        rows = [
            {
                "type": "response_item",
                "payload": {
                    "type": "function_call",
                    "call_id": "batch",
                    "name": "functions.exec",
                    "arguments": (
                        'await tools.exec_command({"cmd":"first"}); '
                        "await tools.exec_command({cmd: computedCommand})"
                    ),
                },
            },
            {
                "type": "response_item",
                "payload": {
                    "type": "function_call_output",
                    "call_id": "batch",
                    "output": json.dumps(
                        {
                            "results": [
                                {"exit_code": 0, "output": "ok"},
                                {"exit_code": 2, "output": "failed"},
                            ]
                        }
                    ),
                },
            },
        ]
        result = AUDIT.audit_codex_session(rows, {"timestamp": "2026-08-12"})
        self.assertEqual(result.shell_outputs, 0)
        self.assertEqual(result.batched_shell_wrappers_uncovered, 1)

    def test_first_boundary_correction(self) -> None:
        rows = [
            {
                "timestamp": "2026-08-01T12:00:00Z",
                "type": "response_item",
                "payload": {
                    "type": "message",
                    "role": "user",
                    "turn_id": "two",
                    "content": [{"type": "input_text", "text": "Still broken"}],
                },
            }
        ]
        session = AUDIT.audit_codex_session(
            rows, {"timestamp": "2026-08-01"}, had_prior_human=True
        )
        self.assertEqual(len(session.corrections), 1)
        self.assertEqual(
            session.corrections[0]["excerpt"],
            "Correction signal: wrong_result",
        )
        self.assertNotIn("Still broken", session.corrections[0]["excerpt"])

    def test_independent_bug_report_is_not_a_correction(self) -> None:
        rows = [
            {
                "type": "response_item",
                "payload": {
                    "type": "message",
                    "role": "user",
                    "turn_id": "one",
                    "content": [{"type": "input_text", "text": "First task"}],
                },
            },
            {
                "type": "response_item",
                "payload": {
                    "type": "message",
                    "role": "user",
                    "turn_id": "two",
                    "content": [{"type": "input_text", "text": "The export is broken"}],
                },
            },
        ]
        result = AUDIT.audit_codex_session(rows, {"timestamp": "2026-08-12"})
        self.assertEqual(result.corrections, [])

    def test_new_work_filter(self) -> None:
        rows = [
            {
                "type": "response_item",
                "payload": {
                    "type": "message",
                    "role": "user",
                    "turn_id": "one",
                    "content": [{"type": "input_text", "text": "First task"}],
                },
            },
            {
                "type": "response_item",
                "payload": {
                    "type": "message",
                    "role": "user",
                    "turn_id": "two",
                    "content": [
                        {"type": "input_text", "text": "Fix the broken exporter"}
                    ],
                },
            },
        ]
        result = AUDIT.audit_codex_session(rows, {"timestamp": "2026-08-12"})
        self.assertEqual(result.corrections, [])

    def test_demonstrative_bug_statement_filter(self) -> None:
        rows = [
            {
                "type": "response_item",
                "payload": {
                    "type": "message",
                    "role": "user",
                    "turn_id": "one",
                    "content": [{"type": "input_text", "text": "First task"}],
                },
            },
            {
                "type": "response_item",
                "payload": {
                    "type": "message",
                    "role": "user",
                    "turn_id": "two",
                    "content": [
                        {"type": "input_text", "text": "This export is broken"}
                    ],
                },
            },
        ]
        result = AUDIT.audit_codex_session(rows, {"timestamp": "2026-08-12"})
        self.assertEqual(result.corrections, [])

    def test_excluded_audit_is_not_prior_human_context(self) -> None:
        audit = {
            "type": "response_item",
            "payload": {
                "type": "message",
                "role": "user",
                "turn_id": "audit",
                "content": [{"type": "input_text", "text": "Audit agent performance"}],
            },
        }
        work = {
            "type": "response_item",
            "payload": {
                "type": "message",
                "role": "user",
                "turn_id": "work",
                "content": [
                    {"type": "input_text", "text": "The login is still broken"}
                ],
            },
        }
        self.assertFalse(
            AUDIT.has_prior_human_message([audit, work], [work], {"audit"})
        )

    def test_error_priority(self) -> None:
        self.assertEqual(
            AUDIT.shell_failure_category("pytest", "pytest: command not found"),
            "invocation_error",
        )
        self.assertEqual(
            AUDIT.shell_failure_category("cmake --build out", "syntax error"),
            "test_or_build",
        )

    def test_common_test_toolchains(self) -> None:
        for command in (
            "npm test",
            "cargo test",
            "go test ./...",
            "dotnet test",
            "python -m unittest",
            "jest",
        ):
            rows = [
                {
                    "type": "response_item",
                    "payload": {
                        "type": "function_call",
                        "call_id": "test",
                        "name": "exec_command",
                        "arguments": json.dumps({"cmd": command}),
                    },
                }
            ]
            result = AUDIT.audit_codex_session(rows, {"timestamp": "2026-08-12"})
            self.assertEqual(result.test_calls, 1, command)

    def test_structured_exit_status(self) -> None:
        success = json.dumps({"exit_code": 0, "output": "command not found"})
        failure = json.dumps({"exit_code": 7, "output": "failed"})
        self.assertEqual(AUDIT.structured_exit_code(success), 0)
        self.assertEqual(AUDIT.structured_exit_code(failure), 7)

    def test_shell_action_inputs(self) -> None:
        patch_call = {"name": "apply_patch", "input": "Never kill 123"}
        shell_call = {
            "name": "exec_command",
            "input": json.dumps({"cmd": 'kill "$upload_pid"'}),
        }
        self.assertEqual(AUDIT.shell_commands(patch_call), [])
        self.assertEqual(AUDIT.shell_commands(shell_call), ['kill "$upload_pid"'])
        wrapper_call = {
            "name": "functions.exec",
            "input": 'const r = tools.exec_command({"cmd":"pytest"})',
        }
        self.assertEqual(AUDIT.shell_commands(wrapper_call), ["pytest"])
        self.assertEqual(
            AUDIT.tool_category("apply_patch", "document exec_command"), "file_edit"
        )
        multi_call = {
            "name": "functions.exec",
            "input": (
                'await tools.exec_command({"cmd":"pytest"}); '
                'await tools.view_image({"path":"image.png"})'
            ),
        }
        self.assertEqual(
            AUDIT.tool_categories_for_call(multi_call["name"], multi_call["input"]),
            ["shell", "visual_ui"],
        )
        self.assertEqual(AUDIT.shell_commands(multi_call), ["pytest"])
        rows = [
            {
                "type": "response_item",
                "payload": {
                    "type": "function_call",
                    "call_id": "multi",
                    "name": multi_call["name"],
                    "arguments": multi_call["input"],
                },
            }
        ]
        result = AUDIT.audit_codex_session(rows, {"timestamp": "2026-08-12"})
        self.assertEqual(result.tool_calls, 2)

    def test_write_stdin_session_link(self) -> None:
        yielded = json.dumps({"session_id": 42, "output": "running"})
        self.assertEqual(AUDIT.session_id_from_output(yielded), "42")
        self.assertEqual(
            AUDIT.session_id_from_input('{"session_id":42,"chars":""}'), "42"
        )

    def test_yielded_exec_wait_links_final_shell_result(self) -> None:
        rows = [
            {
                "type": "response_item",
                "payload": {
                    "type": "function_call",
                    "call_id": "start",
                    "name": "functions.exec",
                    "arguments": 'await tools.exec_command({"cmd":"pytest"})',
                },
            },
            {
                "type": "response_item",
                "payload": {
                    "type": "function_call_output",
                    "call_id": "start",
                    "output": "Script running with cell ID 42",
                },
            },
            {
                "type": "response_item",
                "payload": {
                    "type": "function_call",
                    "call_id": "finish",
                    "name": "wait",
                    "arguments": '{"cell_id":"42"}',
                },
            },
            {
                "type": "response_item",
                "payload": {
                    "type": "function_call_output",
                    "call_id": "finish",
                    "output": '{"exit_code":1,"output":"failed"}',
                },
            },
        ]
        result = AUDIT.audit_codex_session(rows, {"timestamp": "2026-08-12"})
        self.assertEqual(result.shell_outputs, 1)
        self.assertEqual(result.shell_failures, 1)

    def test_turn_id_passthrough_finalizes(self) -> None:
        rows = [
            {
                "type": "event_msg",
                "payload": {
                    "type": "task_started",
                    "internal_chat_message_metadata_passthrough": {"turn_id": "t"},
                },
            },
            {
                "type": "event_msg",
                "payload": {
                    "type": "task_complete",
                    "internal_chat_message_metadata_passthrough": {"turn_id": "t"},
                },
            },
        ]
        result = AUDIT.audit_codex_session(rows, {"timestamp": "2026-08-12"})
        self.assertEqual(result.substantive_turns, 1)

    def test_tool_terminate_is_process_kill(self) -> None:
        rows = [
            {
                "type": "response_item",
                "payload": {
                    "type": "function_call",
                    "call_id": "stop",
                    "name": "wait",
                    "arguments": '{"cell_id":"one","terminate":true}',
                },
            }
        ]
        result = AUDIT.audit_codex_session(rows, {"timestamp": "2026-08-12"})
        self.assertEqual(result.process_kills, 1)

    def test_unrelated_terminate_text_is_not_process_kill(self) -> None:
        rows = [
            {
                "type": "response_item",
                "payload": {
                    "type": "function_call",
                    "call_id": "patch",
                    "name": "apply_patch",
                    "arguments": '{"patch":"add terminate: true"}',
                },
            }
        ]
        result = AUDIT.audit_codex_session(rows, {"timestamp": "2026-08-12"})
        self.assertEqual(result.process_kills, 0)

    def test_baseline_scope(self) -> None:
        current_scope = {
            "repository": "repo",
            "repository_identity": "current-id",
            "window": {"since": "2026-08-01", "until": "2026-08-31"},
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "baseline.json"
            path.write_text(
                json.dumps(
                    {
                        "schema_version": AUDIT.SCHEMA_VERSION,
                        "scope": {
                            "repository": "repo",
                            "repository_identity": "other-id",
                            "window": {"since": "2026-07-01", "until": "2026-07-31"},
                        },
                        "metrics": {},
                    }
                )
            )
            with self.assertRaises(AUDIT.AuditError):
                AUDIT.build_comparison({}, current_scope, path)

    def test_baseline_allows_different_checkout_label(self) -> None:
        current_scope = {
            "repository": "worktree-name",
            "repository_identity": "same-id",
            "window": {"since": "2026-08-01", "until": "2026-08-31"},
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "baseline.json"
            path.write_text(
                json.dumps(
                    {
                        "schema_version": AUDIT.SCHEMA_VERSION,
                        "scope": {
                            "repository": "primary-name",
                            "repository_identity": "same-id",
                            "window": {"since": "2026-07-01", "until": "2026-07-31"},
                        },
                        "metrics": {},
                    }
                )
            )
            comparison = AUDIT.build_comparison({}, current_scope, path)
        self.assertIsNotNone(comparison)

    def test_privacy_validator_rejects_source_paths(self) -> None:
        with self.assertRaises(AUDIT.AuditError):
            AUDIT.validate_privacy({"path": "/Users/person/.codex/sessions/raw.jsonl"})

    def test_case_notes_are_redacted(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "notes.json"
            path.write_text(
                json.dumps(
                    [
                        {
                            "title": "Upload",
                            "cause": "Read /Users/person/private.txt",
                            "control": "Use local recovery",
                            "status": "controlled",
                        }
                    ]
                )
            )
            notes = AUDIT.load_case_notes(path)
        self.assertEqual(notes[0]["cause"], "Read [path]")


if __name__ == "__main__":
    unittest.main()
