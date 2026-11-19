"""Tests for the lockfile's `commit` field: required by --check, compared by the drift check."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from fixtures import canonical, git, make_fixture, make_marketplace_clone

REPO_ROOT = Path(__file__).resolve().parent.parent
GENERATE = REPO_ROOT / "scripts" / "generate.py"
DRIFT_CHECK = REPO_ROOT / "scripts" / "check-plugin-drift.py"

sys.path.insert(0, str(REPO_ROOT / "scripts"))
from lib.vendored_plugins import LOCKFILE, MARKETPLACE, PLUGIN  # noqa: E402

FULL_SHA = "6acc160e4e0cd062dbbbd7a1b26ae92855edf07e"
NO_COMMIT = object()


def write_lock(root: Path, commit: object = FULL_SHA) -> None:
    lock = {"marketplace": MARKETPLACE, "plugin": PLUGIN, "ref": "v1.2.3", "skills": {}}
    if commit is not NO_COMMIT:
        lock["commit"] = commit
    (root / LOCKFILE).parent.mkdir(parents=True, exist_ok=True)
    (root / LOCKFILE).write_text(canonical(lock))


class CheckRequiresTheCommit(unittest.TestCase):
    """generate.py --check reads only the committed lockfile, so this holds in CI."""

    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        make_fixture(self.root, settings_hooks={}, source_hooks={})
        settings = json.loads((self.root / "settings.json").read_text())
        settings["extraKnownMarketplaces"] = {
            MARKETPLACE: {"source": {"source": "github", "repo": "example/repo", "ref": "v1.2.3"}}
        }
        (self.root / "settings.json").write_text(canonical(settings))

    def check(self) -> subprocess.CompletedProcess:
        return subprocess.run(
            [
                sys.executable,
                str(GENERATE),
                "--root",
                str(self.root),
                "--check",
                "--only",
                "settings-hooks",
            ],
            capture_output=True,
            text=True,
        )

    def assert_rejected(self) -> None:
        result = self.check()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("commit", result.stderr)
        self.assertIn(str(LOCKFILE), result.stderr)

    def test_full_sha_passes(self) -> None:
        write_lock(self.root)
        result = self.check()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_missing_commit_fails(self) -> None:
        write_lock(self.root, commit=NO_COMMIT)
        self.assert_rejected()

    def test_abbreviated_commit_fails(self) -> None:
        write_lock(self.root, commit=FULL_SHA[:12])
        self.assert_rejected()

    def test_non_hex_commit_fails(self) -> None:
        write_lock(self.root, commit="z" * 40)
        self.assert_rejected()

    def test_uppercase_or_non_string_commit_fails(self) -> None:
        for commit in (FULL_SHA.upper(), 12345, None):
            with self.subTest(commit=commit):
                write_lock(self.root, commit=commit)
                self.assert_rejected()


class DriftCheck(unittest.TestCase):
    """The local check compares the marketplace clone's HEAD with the lockfile."""

    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name) / "repo"
        self.clones = Path(tmp.name) / "marketplaces"
        self.root.mkdir()

    def run_check(self, **env: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [
                sys.executable,
                str(DRIFT_CHECK),
                "--root",
                str(self.root),
                "--marketplaces",
                str(self.clones),
            ],
            capture_output=True,
            text=True,
            env={**os.environ, **env},
        )

    def test_reads_the_clone_even_when_git_points_the_hook_at_this_repo(self) -> None:
        # Git exports GIT_DIR to a hook it runs from a linked worktree, and
        # that would outrank `-C`: the check would compare this repo's HEAD.
        head = make_marketplace_clone(self.clones, MARKETPLACE, tags=("v1.2.3",))
        make_marketplace_clone(self.clones, "some-other-repo")
        git(self.clones / "some-other-repo", "commit", "-q", "--allow-empty", "-m", "elsewhere")
        self.assertNotEqual(head, git(self.clones / "some-other-repo", "rev-parse", "HEAD"))
        write_lock(self.root, commit=head)
        result = self.run_check(GIT_DIR=str(self.clones / "some-other-repo" / ".git"))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("OK", result.stdout)

    def test_passes_when_head_is_the_locked_commit(self) -> None:
        head = make_marketplace_clone(self.clones, MARKETPLACE, tags=("v1.2.3",))
        write_lock(self.root, commit=head)
        result = self.run_check()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn("SKIPPED", result.stdout)

    def test_fails_naming_both_commits_when_head_has_moved(self) -> None:
        locked = make_marketplace_clone(self.clones, MARKETPLACE, tags=("v1.2.3",))
        git(self.clones / MARKETPLACE, "commit", "-q", "--allow-empty", "-m", "re-cut")
        moved = git(self.clones / MARKETPLACE, "rev-parse", "HEAD")
        write_lock(self.root, commit=locked)
        result = self.run_check()
        output = result.stdout + result.stderr
        self.assertEqual(result.returncode, 1, output)
        self.assertIn(locked, output)
        self.assertIn(moved, output)
        self.assertIn("Bumping a vendored plugin", output)

    def test_skips_with_a_message_when_there_is_no_clone(self) -> None:
        write_lock(self.root)
        result = self.run_check()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("SKIPPED", result.stdout)

    def test_a_plain_directory_is_not_mistaken_for_a_clone(self) -> None:
        (self.clones / MARKETPLACE).mkdir(parents=True)
        write_lock(self.root)
        result = self.run_check()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("SKIPPED", result.stdout)

    def test_skips_when_the_repo_pins_nothing(self) -> None:
        make_marketplace_clone(self.clones, MARKETPLACE)
        result = self.run_check()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("SKIPPED", result.stdout)


if __name__ == "__main__":
    unittest.main()
