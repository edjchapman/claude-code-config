"""CLI tests for scripts/generate.py (ADR-0001).

The generator's CLI is its interface and therefore the test surface: every
test builds a fixture repo root, invokes the CLI as a subprocess, and asserts
on exit codes and resulting file bytes — never on internals.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
GENERATE = REPO_ROOT / "scripts" / "generate.py"


def canonical(obj: dict) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=False) + "\n"


HOOK_ENTRY = [
    {
        "hooks": [
            {
                "type": "command",
                "command": "${CLAUDE_PLUGIN_DIR:-fallback}/scripts/hooks/session-context.sh",
            }
        ]
    }
]


def make_fixture(root: Path, settings_hooks: dict, source_hooks: dict) -> None:
    """Write a minimal repo root: settings.json + hooks/hooks.json."""
    (root / "hooks").mkdir()
    (root / "hooks" / "hooks.json").write_text(
        canonical({"$schema": "https://example.invalid/schema.json", "hooks": source_hooks})
    )
    (root / "settings.json").write_text(
        canonical(
            {
                "$schema": "https://example.invalid/schema.json",
                "attribution": {"commit": "", "pr": "", "sessionUrl": False},
                "hooks": settings_hooks,
                "tui": "fullscreen",
                "autoMemoryEnabled": False,
            }
        )
    )


def run_generate(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(GENERATE), "--root", str(root), *args],
        capture_output=True,
        text=True,
    )


class StaleHooksBlock(unittest.TestCase):
    """A settings.json hooks block that lags hooks/hooks.json."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)
        make_fixture(
            self.root,
            settings_hooks={"SessionStart": HOOK_ENTRY},
            source_hooks={"SessionStart": HOOK_ENTRY, "SessionEnd": HOOK_ENTRY},
        )

    def test_check_fails_naming_the_stale_file(self) -> None:
        result = run_generate(self.root, "--check")
        self.assertEqual(result.returncode, 1)
        self.assertIn("settings.json", result.stdout + result.stderr)

    def test_write_mode_fixes_then_check_passes(self) -> None:
        write = run_generate(self.root)
        self.assertEqual(write.returncode, 0)
        updated = json.loads((self.root / "settings.json").read_text())
        self.assertIn("SessionEnd", updated["hooks"])
        check = run_generate(self.root, "--check")
        self.assertEqual(check.returncode, 0, check.stdout + check.stderr)


class PreservationAndIdempotency(unittest.TestCase):
    """Non-hooks content survives byte-for-byte; regeneration converges."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)
        make_fixture(
            self.root,
            settings_hooks={},
            source_hooks={"SessionStart": HOOK_ENTRY},
        )

    def test_only_the_hooks_block_changes(self) -> None:
        before = json.loads((self.root / "settings.json").read_text())
        run_generate(self.root)
        after_text = (self.root / "settings.json").read_text()
        after = json.loads(after_text)
        self.assertEqual(after["hooks"], {"SessionStart": HOOK_ENTRY})
        before["hooks"] = {"SessionStart": HOOK_ENTRY}
        self.assertEqual(after_text, canonical(before))

    def test_second_run_is_a_byte_level_noop(self) -> None:
        run_generate(self.root)
        first = (self.root / "settings.json").read_bytes()
        second_run = run_generate(self.root)
        self.assertEqual(second_run.returncode, 0)
        self.assertIn("up to date", second_run.stdout)
        self.assertEqual((self.root / "settings.json").read_bytes(), first)

    def test_in_sync_fixture_passes_check_untouched(self) -> None:
        run_generate(self.root)
        before = (self.root / "settings.json").read_bytes()
        check = run_generate(self.root, "--check")
        self.assertEqual(check.returncode, 0)
        self.assertEqual((self.root / "settings.json").read_bytes(), before)


class CliContract(unittest.TestCase):
    """Interface details a caller (pre-commit, CI, a human) relies on."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)

    def test_only_selects_a_known_target(self) -> None:
        make_fixture(self.root, settings_hooks={}, source_hooks={"SessionStart": HOOK_ENTRY})
        result = run_generate(self.root, "--only", "settings-hooks")
        self.assertEqual(result.returncode, 0)
        updated = json.loads((self.root / "settings.json").read_text())
        self.assertIn("SessionStart", updated["hooks"])

    def test_unknown_target_is_rejected(self) -> None:
        result = run_generate(self.root, "--only", "no-such-target")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("no-such-target", result.stderr)

    def test_missing_source_fails_with_a_named_error(self) -> None:
        (self.root / "settings.json").write_text(canonical({"hooks": {}}))
        result = run_generate(self.root, "--check")
        self.assertEqual(result.returncode, 1)
        self.assertIn("hooks.json", result.stderr)


if __name__ == "__main__":
    unittest.main()
