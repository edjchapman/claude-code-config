"""CLI tests for scripts/sync-global-settings.py (ADR-0002).

Same philosophy as test_generate.py: the CLI is the interface, so every
test builds a fixture source root and target file, invokes the script as a
subprocess, and asserts on exit codes and resulting file bytes — never on
internals.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SYNC = REPO_ROOT / "scripts" / "sync-global-settings.py"

# A minimal source settings.json of repo-managed keys (all in ALLOWED_KEYS).
SOURCE = {
    "tui": "fullscreen",
    "outputStyle": "Explanatory",
    "enabledPlugins": {
        "github@official": True,
        "feature-dev@official": False,
    },
}


def run_sync(source_root: Path, target: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [
            sys.executable,
            str(SYNC),
            "--source-root",
            str(source_root),
            "--target",
            str(target),
            *args,
        ],
        capture_output=True,
        text=True,
    )


class SyncGlobalSettings(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)
        self.source_root = self.root / "repo"
        self.source_root.mkdir()
        self.target = self.root / "home" / "settings.json"
        self.target.parent.mkdir()
        self.write_source(SOURCE)

    def write_source(self, config: dict) -> None:
        (self.source_root / "settings.json").write_text(json.dumps(config))

    def write_target(self, config: dict) -> None:
        self.target.write_text(json.dumps(config))

    def read_target(self) -> dict:
        return json.loads(self.target.read_text())

    def test_managed_keys_mirror_and_personal_keys_survive(self) -> None:
        self.write_target(
            {
                "tui": "inline",  # managed, diverged: repo wins
                "model": "fable",  # personal: untouched
                "permissions": {"allow": ["Bash(ls:*)"]},  # personal: untouched
            }
        )
        result = run_sync(self.source_root, self.target)
        self.assertEqual(result.returncode, 0, result.stderr)
        merged = self.read_target()
        self.assertEqual(merged["tui"], "fullscreen")
        self.assertEqual(merged["model"], "fable")
        self.assertEqual(merged["permissions"], {"allow": ["Bash(ls:*)"]})

    def test_dropped_managed_key_is_deleted(self) -> None:
        # outputStyle is in ALLOWED_KEYS; a repo that stops shipping it
        # cleans it out of the home file.
        self.write_target({"outputStyle": "Explanatory", "model": "fable"})
        self.write_source({"tui": "fullscreen"})
        run_sync(self.source_root, self.target)
        merged = self.read_target()
        self.assertNotIn("outputStyle", merged)
        self.assertEqual(merged["model"], "fable")

    def test_enabled_plugins_merge_per_entry(self) -> None:
        self.write_target(
            {
                "enabledPlugins": {
                    "feature-dev@official": True,  # repo default-off: reverted
                    "figma@personal": True,  # personal: preserved
                }
            }
        )
        run_sync(self.source_root, self.target)
        plugins = self.read_target()["enabledPlugins"]
        self.assertEqual(plugins["feature-dev@official"], False)
        self.assertEqual(plugins["github@official"], True)
        self.assertEqual(plugins["figma@personal"], True)

    def test_symlinked_target_becomes_real_file(self) -> None:
        os.symlink(self.source_root / "settings.json", self.target)
        result = run_sync(self.source_root, self.target)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(self.target.is_symlink())
        self.assertEqual(self.read_target()["tui"], "fullscreen")

    def test_missing_target_is_created_with_managed_keys_only(self) -> None:
        result = run_sync(self.source_root, self.target)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.read_target(), SOURCE)

    def test_idempotent_second_run_reports_in_sync(self) -> None:
        run_sync(self.source_root, self.target)
        second = run_sync(self.source_root, self.target)
        self.assertEqual(second.returncode, 0)
        self.assertIn("already in sync", second.stdout)

    def test_check_warns_on_drift_and_exits_zero(self) -> None:
        self.write_target({"tui": "inline"})
        result = run_sync(self.source_root, self.target, "--check")
        self.assertEqual(result.returncode, 0)
        self.assertIn("drifted", result.stdout)
        # Warn-only: the target must not have been modified.
        self.assertEqual(self.read_target(), {"tui": "inline"})

    def test_check_is_silent_when_in_sync(self) -> None:
        run_sync(self.source_root, self.target)
        result = run_sync(self.source_root, self.target, "--check")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")

    def test_unparseable_target_is_never_clobbered(self) -> None:
        self.target.write_text("{not json")
        apply_run = run_sync(self.source_root, self.target)
        self.assertEqual(apply_run.returncode, 1)
        self.assertEqual(self.target.read_text(), "{not json")
        check_run = run_sync(self.source_root, self.target, "--check")
        self.assertEqual(check_run.returncode, 0)


if __name__ == "__main__":
    unittest.main()
