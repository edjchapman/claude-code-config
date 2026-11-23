"""Tests for the vendored-plugin lockfile generator, against a temporary plugin cache."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from fixtures import git, make_marketplace_clone

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "update-plugin-lock.py"

sys.path.insert(0, str(REPO_ROOT / "scripts"))
from lib.vendored_plugins import (  # noqa: E402
    LOCKFILE,
    MARKETPLACE,
    PLUGIN,
    VendoredPlugin,
    plugin_cache_root,
)

PLUGIN_UNDER_TEST = VendoredPlugin(MARKETPLACE, PLUGIN, "example/repo", "v0.0.0")


def add_cached_version(cache: Path, directory: str, version: str | None = None) -> Path:
    """Lay down one cached plugin version shipping a single model-invocable skill."""
    root = cache / MARKETPLACE / PLUGIN / directory
    (root / ".claude-plugin").mkdir(parents=True)
    (root / ".claude-plugin" / "plugin.json").write_text(
        json.dumps({"version": version or directory, "skills": ["./skills/alpha"]})
    )
    (root / "skills" / "alpha").mkdir(parents=True)
    (root / "skills" / "alpha" / "SKILL.md").write_text(
        f"---\nname: alpha\ndescription: Alpha from {version or directory}.\n---\nbody\n"
    )
    return root


class TempDirs(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.cache = Path(tmp.name) / "cache"
        self.clones = Path(tmp.name) / "marketplaces"
        self.root = Path(tmp.name) / "repo"
        self.cache.mkdir()
        self.root.mkdir()


class CacheVersionOrdering(TempDirs):
    def test_versions_order_numerically_not_lexically(self) -> None:
        for version in ("1.2.0", "1.2.3", "1.10.0"):
            add_cached_version(self.cache, version)
        self.assertEqual(plugin_cache_root(PLUGIN_UNDER_TEST, self.cache).name, "1.10.0")

    def test_a_longer_version_outranks_its_prefix(self) -> None:
        for version in ("1.2", "1.2.1"):
            add_cached_version(self.cache, version)
        self.assertEqual(plugin_cache_root(PLUGIN_UNDER_TEST, self.cache).name, "1.2.1")

    def test_non_numeric_names_do_not_raise_or_outrank_a_version(self) -> None:
        for name in ("1.2.3", "1.10.0", "1.11.0-beta", "zz-stray"):
            add_cached_version(self.cache, name)
        self.assertEqual(plugin_cache_root(PLUGIN_UNDER_TEST, self.cache).name, "1.10.0")

    def test_only_non_numeric_names_still_resolve(self) -> None:
        add_cached_version(self.cache, "main")
        self.assertEqual(plugin_cache_root(PLUGIN_UNDER_TEST, self.cache).name, "main")


class GeneratorCase(TempDirs):
    def run_script(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--root",
                str(self.root),
                "--cache",
                str(self.cache),
                "--marketplaces",
                str(self.clones),
                *args,
            ],
            capture_output=True,
            text=True,
        )

    @property
    def lockfile(self) -> Path:
        return self.root / LOCKFILE


class RefMustNameTheCachedVersion(GeneratorCase):
    def setUp(self) -> None:
        super().setUp()
        make_marketplace_clone(self.clones, MARKETPLACE, tags=("v1.10.0", "1.10.0"))

    def test_mismatch_fails_names_both_and_leaves_the_lockfile_alone(self) -> None:
        add_cached_version(self.cache, "1.2.3")
        self.lockfile.parent.mkdir(parents=True)
        self.lockfile.write_text("EXISTING LOCKFILE\n")
        result = self.run_script("--ref", "v1.10.0")
        output = result.stdout + result.stderr
        self.assertNotEqual(result.returncode, 0, output)
        self.assertIn("v1.10.0", output)
        self.assertIn("1.2.3", output)
        self.assertEqual(self.lockfile.read_text(), "EXISTING LOCKFILE\n")

    def test_mismatch_writes_no_lockfile_where_none_existed(self) -> None:
        add_cached_version(self.cache, "1.2.3")
        result = self.run_script("--ref", "1.10.0")
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse(self.lockfile.exists())

    def test_the_check_reads_plugin_json_not_the_directory_name(self) -> None:
        add_cached_version(self.cache, "1.10.0", version="1.2.3")
        result = self.run_script("--ref", "v1.10.0")
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse(self.lockfile.exists())

    def test_matching_ref_writes_the_lockfile(self) -> None:
        for version in ("1.2.3", "1.10.0"):
            add_cached_version(self.cache, version)
        for ref in ("v1.10.0", "1.10.0"):
            with self.subTest(ref=ref):
                result = self.run_script("--ref", ref)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertNotIn("not verified", result.stdout + result.stderr)
                lock = json.loads(self.lockfile.read_text())
                self.assertEqual(lock["ref"], ref)
                self.assertEqual(lock["version"], "1.10.0")
                self.assertEqual(
                    lock["skills"],
                    {"alpha": {"description": "Alpha from 1.10.0.", "model_invocable": True}},
                )
                self.assertEqual(lock["always_loaded_bytes"], len(b"Alpha from 1.10.0."))

    def test_branch_ref_is_accepted_and_reported_as_unverified(self) -> None:
        add_cached_version(self.cache, "1.2.3")
        result = self.run_script("--ref", "main")
        output = result.stdout + result.stderr
        self.assertEqual(result.returncode, 0, output)
        self.assertIn("version not verified", output)
        self.assertEqual(json.loads(self.lockfile.read_text())["ref"], "main")


class CommitIsRecorded(GeneratorCase):
    """The lockfile names the commit the pinned ref resolved to (issue #156)."""

    def setUp(self) -> None:
        super().setUp()
        add_cached_version(self.cache, "1.2.3")
        self.head = make_marketplace_clone(self.clones, MARKETPLACE, tags=("v1.2.3",))

    def test_commit_is_the_clones_head_written_beside_ref(self) -> None:
        result = self.run_script("--ref", "v1.2.3")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        lock = json.loads(self.lockfile.read_text())
        self.assertEqual(lock["commit"], self.head)
        self.assertEqual(len(lock["commit"]), 40)
        keys = list(lock)
        self.assertEqual(keys.index("commit"), keys.index("ref") + 1)

    def test_a_branch_ref_records_the_commit_too(self) -> None:
        result = self.run_script("--ref", "main")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(json.loads(self.lockfile.read_text())["commit"], self.head)

    def test_clone_off_the_ref_is_refused_and_nothing_is_written(self) -> None:
        git(self.clones / MARKETPLACE, "commit", "-q", "--allow-empty", "-m", "moved on")
        moved = git(self.clones / MARKETPLACE, "rev-parse", "HEAD")
        self.lockfile.parent.mkdir(parents=True)
        self.lockfile.write_text("EXISTING LOCKFILE\n")
        result = self.run_script("--ref", "v1.2.3")
        output = result.stdout + result.stderr
        self.assertNotEqual(result.returncode, 0, output)
        self.assertIn(self.head, output)
        self.assertIn(moved, output)
        self.assertEqual(self.lockfile.read_text(), "EXISTING LOCKFILE\n")

    def test_a_ref_the_clone_does_not_know_is_refused(self) -> None:
        git(self.clones / MARKETPLACE, "tag", "-d", "v1.2.3")
        result = self.run_script("--ref", "v1.2.3")
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse(self.lockfile.exists())

    def test_no_clone_is_refused(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--root",
                str(self.root),
                "--cache",
                str(self.cache),
                "--marketplaces",
                str(self.clones / "absent"),
                "--ref",
                "v1.2.3",
            ],
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("marketplace clone", result.stdout + result.stderr)
        self.assertFalse(self.lockfile.exists())


if __name__ == "__main__":
    unittest.main()
