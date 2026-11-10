"""Behavioural tests for scripts/hooks/stop-check.sh, run against throwaway git repos."""

import json
import os
import pathlib
import subprocess
import tempfile
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
HOOK = REPO_ROOT / "scripts" / "hooks" / "stop-check.sh"


class StopCheckCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        base = pathlib.Path(self._tmp.name)
        self.repo = base / "repo"
        self.state = base / "state"
        self.repo.mkdir()
        self.state.mkdir()
        self.git("init", "-q")
        (self.repo / "app.txt").write_text("v1\n")
        # The check passes unless app.txt contains "broken"; it also counts its runs.
        self.opt_in("! grep -q broken app.txt; s=$?; echo run >> ../runs; exit $s")
        self.git("add", ".")
        self.git("commit", "-qm", "init")

    def tearDown(self):
        self._tmp.cleanup()

    def git(self, *args):
        subprocess.run(
            ["git", "-c", "user.name=t", "-c", "user.email=t@t", *args],
            cwd=self.repo,
            check=True,
            capture_output=True,
        )

    def opt_in(self, command):
        (self.repo / ".claude").mkdir(exist_ok=True)
        (self.repo / ".claude" / "stop-check").write_text(f"# check\n{command}\n")

    def stop(self, session="s1", **env):
        proc = subprocess.run(
            [str(HOOK)],
            input=json.dumps({"session_id": session, "cwd": str(self.repo)}),
            capture_output=True,
            text=True,
            env={**os.environ, "TMPDIR": str(self.state), **env},
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return json.loads(proc.stdout) if proc.stdout.strip() else {}

    def runs(self):
        runs = self.repo.parent / "runs"
        return len(runs.read_text().splitlines()) if runs.exists() else 0

    def edit(self, text):
        (self.repo / "app.txt").write_text(text)


class TestGating(StopCheckCase):
    def test_clean_tree_on_first_stop_is_trusted(self):
        self.assertFalse(self.stop())
        self.assertEqual(self.runs(), 0)

    def test_no_opt_in_file_means_no_check(self):
        (self.repo / ".claude" / "stop-check").unlink()
        self.edit("broken\n")
        self.assertFalse(self.stop())
        self.assertEqual(self.runs(), 0)

    def test_disable_env(self):
        self.edit("broken\n")
        self.assertFalse(self.stop(CLAUDE_STOP_CHECK="0"))

    def test_outside_git_and_bad_payload_fail_open(self):
        proc = subprocess.run(
            [str(HOOK)], input="not json", capture_output=True, text=True, cwd=tempfile.gettempdir()
        )
        self.assertEqual((proc.returncode, proc.stdout), (0, ""))

    def test_unchanged_tree_after_pass_is_not_rerun(self):
        self.edit("v2\n")
        self.assertFalse(self.stop())
        self.assertFalse(self.stop())
        self.assertEqual(self.runs(), 1)

    def test_new_untracked_file_counts_as_change(self):
        self.edit("v2\n")
        self.stop()
        (self.repo / "new.txt").write_text("x")
        self.stop()
        (self.repo / "new.txt").write_text("y")
        self.stop()
        self.assertEqual(self.runs(), 3)


class TestBlocking(StopCheckCase):
    def test_failure_blocks_with_output(self):
        self.edit("broken\n")
        out = self.stop()
        self.assertEqual(out["decision"], "block")
        self.assertIn("failed (exit 1)", out["reason"])

    def test_same_failing_tree_is_reported_once(self):
        self.edit("broken\n")
        self.assertEqual(self.stop()["decision"], "block")
        self.assertFalse(self.stop())
        self.assertEqual(self.runs(), 1)

    def test_fix_clears_the_block(self):
        self.edit("broken\n")
        self.stop()
        self.edit("fixed\n")
        self.assertFalse(self.stop())

    def test_gives_up_after_max_blocks(self):
        for i in range(3):
            self.edit(f"broken {i}\n")
            self.assertEqual(self.stop()["decision"], "block")
        self.edit("broken 3\n")
        out = self.stop()
        self.assertNotIn("decision", out)
        self.assertIn("still failing", out["systemMessage"])

    def test_sessions_are_independent(self):
        self.edit("broken\n")
        self.stop("a")
        self.assertEqual(self.stop("b")["decision"], "block")


if __name__ == "__main__":
    unittest.main()
