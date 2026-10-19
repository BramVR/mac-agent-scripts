#!/usr/bin/env python3
"""Exercise the launcher with a fake Claude executable and no API calls."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parent.parent
WRAPPER = ROOT / "scripts/t3-claude"
PRESET = json.loads((ROOT / "config/t3-pstack/claude-t3-settings.json").read_text())


class LauncherTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="t3 claude ")
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.capture = self.directory / "argv.json"
        self.binary = self.directory / "claude"
        self.binary.write_text(
            f"#!{sys.executable}\n"
            "import json, os, pathlib, sys\n"
            "pathlib.Path(os.environ['T3_TEST_CAPTURE']).write_text(json.dumps(sys.argv[1:]))\n"
            "sys.stdout.buffer.write(b'Claude version fake\\n\\xff')\n"
            "sys.stderr.buffer.write(b'native stderr\\n\\xfe')\n"
            "sys.exit(int(os.environ.get('T3_TEST_EXIT', '0')))\n"
        )
        self.binary.chmod(0o755)
        self.environment = dict(os.environ)
        self.environment.update(
            T3_PSTACK_CLAUDE_BINARY=str(self.binary),
            T3_TEST_CAPTURE=str(self.capture),
            T3_TEST_EXIT="0",
        )

    def run_wrapper(self, *arguments, wrapper=WRAPPER):
        return subprocess.run(
            [str(wrapper), *arguments],
            env=self.environment,
            cwd=self.directory,
            capture_output=True,
            timeout=10,
        )

    def captured(self):
        arguments = json.loads(self.capture.read_text())
        self.assertEqual(arguments[0], "--settings")
        return json.loads(arguments[1]), arguments[2:]

    def test_sdk_settings_and_preset_merge(self):
        sdk = {
            "fastMode": False,
            "showThinkingSummaries": True,
            "permissions": {"allow": ["Read"]},
            "enabledPlugins": {"unrelated@example": True, "t3-pstack@t3-pstack": False},
            "skillOverrides": {"unrelated": "on", "poteto-mode": "on"},
        }
        result = self.run_wrapper("--settings", json.dumps(sdk), "--print", "hello")
        self.assertEqual(result.returncode, 0, result.stderr)
        merged, forwarded = self.captured()
        self.assertEqual(forwarded, ["--print", "hello"])
        self.assertIs(merged["fastMode"], False)
        self.assertIs(merged["showThinkingSummaries"], True)
        self.assertEqual(merged["permissions"], sdk["permissions"])
        self.assertEqual(merged["enabledPlugins"], {**sdk["enabledPlugins"], **PRESET["enabledPlugins"]})
        self.assertEqual(merged["skillOverrides"], {**sdk["skillOverrides"], **PRESET["skillOverrides"]})
        self.assertEqual(len(PRESET["skillOverrides"]), 58)
        self.assertIs(merged["enabledPlugins"]["t3-pstack@t3-pstack"], True)

    def test_settings_file_with_spaces_and_both_flag_forms(self):
        settings_file = self.directory / "settings with spaces=extra.json"
        settings_file.write_text(json.dumps({"fastMode": False, "custom": [1, "two"]}))
        for flags in (["--settings", str(settings_file)], ["--settings=" + str(settings_file)]):
            with self.subTest(flags=flags):
                result = self.run_wrapper(*flags)
                self.assertEqual(result.returncode, 0, result.stderr)
                merged, forwarded = self.captured()
                self.assertEqual(merged["custom"], [1, "two"])
                self.assertIs(merged["fastMode"], False)
                self.assertEqual(forwarded, [])

    def test_repeated_settings_and_inline_equals_form(self):
        result = self.run_wrapper(
            "--settings", '{"first":1,"enabledPlugins":{"one":true}}',
            '--settings={"second":2,"enabledPlugins":{"two":false}}',
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        merged, forwarded = self.captured()
        self.assertEqual((merged["first"], merged["second"]), (1, 2))
        self.assertEqual(merged["enabledPlugins"], {"one": True, "two": False, **PRESET["enabledPlugins"]})
        self.assertEqual(forwarded, [])

    def test_forwarded_arguments_are_unchanged(self):
        arguments = [
            "--print", "", "two words", "$(touch never-created)", "; | & > < `echo x`",
            "quotes'\"", "line\nbreak", "café", os.fsdecode(b"raw-\xff"),
            "--settings-like=keep", "--", "--settings", "literal", "--settings=literal",
        ]
        result = self.run_wrapper(*arguments)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.captured()[1], arguments)
        self.assertFalse((self.directory / "never-created").exists())

    def test_native_output_and_exit_status(self):
        self.environment["T3_TEST_EXIT"] = "23"
        result = self.run_wrapper("--version")
        self.assertEqual(result.returncode, 23)
        self.assertEqual(result.stdout, b"Claude version fake\n\xff")
        self.assertEqual(result.stderr, b"native stderr\n\xfe")
        self.assertEqual(self.captured(), (PRESET, ["--version"]))

    def test_path_lookup_and_resolved_wrapper_location(self):
        self.environment.pop("T3_PSTACK_CLAUDE_BINARY")
        self.environment["PATH"] = str(self.directory) + os.pathsep + os.environ.get("PATH", "")
        alias = self.directory / "launcher"
        alias.symlink_to(WRAPPER)
        result = self.run_wrapper("--version", wrapper=alias)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.captured(), (PRESET, ["--version"]))

    def test_invalid_settings_fail_before_launch(self):
        invalid_file = self.directory / "invalid.json"
        invalid_file.write_text('{"sensitive-marker": broken}')
        invalid_utf8 = self.directory / "invalid-utf8.json"
        invalid_utf8.write_bytes(b"\xff")
        for flags in (
            ["--settings"], ["--settings", "--version"], ["--settings="],
            ["--settings", '{"sensitive-marker": broken}'],
            ["--settings", str(self.directory / "missing-sensitive-marker.json")],
            ["--settings", str(invalid_file)], ["--settings", str(invalid_utf8)],
            ["--settings", "[]"], ["--settings", "null"],
            ["--settings", '{"enabledPlugins":false}'],
            ["--settings", '{"skillOverrides":[]}'],
        ):
            with self.subTest(flags=flags):
                result = self.run_wrapper(*flags)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(result.stdout, b"")
                self.assertTrue(result.stderr.startswith(b"t3-claude: "))
                self.assertNotIn(b"sensitive-marker", result.stderr)
                self.assertNotIn(b"Traceback", result.stderr)
                self.assertFalse(self.capture.exists())

    def test_recursive_executable_rejected(self):
        alias = self.directory / "recursive-claude"
        alias.symlink_to(WRAPPER)
        hardlink = self.directory / "hardlink-claude"
        hardlink.hardlink_to(WRAPPER)
        for binary in (WRAPPER, alias, hardlink):
            with self.subTest(binary=binary):
                self.environment["T3_PSTACK_CLAUDE_BINARY"] = str(binary)
                result = self.run_wrapper("--version")
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(result.stdout, b"")
                self.assertIn(b"t3-claude:", result.stderr)
                self.assertFalse(self.capture.exists())

    def test_unavailable_executable_rejected(self):
        for binary in ("", str(self.directory / "missing-claude"), str(self.directory)):
            with self.subTest(binary=binary):
                self.environment["T3_PSTACK_CLAUDE_BINARY"] = binary
                result = self.run_wrapper("--version")
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse(self.capture.exists())


if __name__ == "__main__":
    unittest.main()
