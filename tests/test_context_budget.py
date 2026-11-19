"""Tests for check-context-budget.py's repo check, run against this repo's own primitives."""

import pathlib
import subprocess
import sys
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "check-context-budget.py"


class TestRepoBudget(unittest.TestCase):
    def test_a_user_only_skill_costs_no_always_loaded_context(self):
        # `later` sets disable-model-invocation: true, so its description is
        # never loaded into a session; `commit` does not, so its is.
        out = subprocess.run([sys.executable, str(SCRIPT)], capture_output=True, text=True).stdout

        self.assertIn("skills/commit/SKILL.md (description)", out)
        self.assertNotIn("skills/later/SKILL.md", out)


if __name__ == "__main__":
    unittest.main()
