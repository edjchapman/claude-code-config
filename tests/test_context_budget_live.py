"""Tests for check-context-budget.py --live, driven through a stub `claude` CLI."""

import json
import os
import pathlib
import stat
import subprocess
import sys
import tempfile
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "check-context-budget.py"

STUB = """#!/bin/sh
if [ "$2" = "list" ]; then
  cat <<'JSON'
{plugins}
JSON
else
  echo "Projected token cost"
  case "$3" in
    {cases}
  esac
fi
"""


def run_live(plugins, stub=True):
    """Run --live with PATH holding only a stub CLI built from {id: (enabled, details)}."""
    with tempfile.TemporaryDirectory() as tmp:
        if stub:
            listing = [{"id": name, "enabled": on} for name, (on, _) in plugins.items()]
            cases = "\n    ".join(
                f'"{name}") echo "{details}" ;;' for name, (_, details) in plugins.items()
            )
            path = pathlib.Path(tmp) / "claude"
            path.write_text(STUB.format(plugins=json.dumps(listing), cases=cases))
            path.chmod(path.stat().st_mode | stat.S_IEXEC)
        proc = subprocess.run(
            [sys.executable, str(SCRIPT), "--live"],
            capture_output=True,
            text=True,
            env={**os.environ, "PATH": f"{tmp}:/usr/bin:/bin"},
        )
    return proc.returncode, proc.stdout


class TestLiveBudget(unittest.TestCase):
    def test_under_budget_passes(self):
        code, out = run_live({"small@x": (True, "  Always-on:   ~1,622 tok   added")})
        self.assertEqual(code, 0, out)
        self.assertIn("small@x", out)

    def test_over_budget_fails_and_names_the_plugin(self):
        code, out = run_live({"huge@synced": (True, "  Always-on:   ~11,679 tok   added")})
        self.assertEqual(code, 1, out)
        self.assertIn("huge@synced", out)

    def test_disabled_plugins_are_not_counted(self):
        code, out = run_live(
            {
                "huge@synced": (False, "  Always-on:   ~11,679 tok"),
                "small@x": (True, "  Always-on:   ~100 tok"),
            }
        )
        self.assertEqual(code, 0, out)
        self.assertNotIn("huge@synced", out)

    def test_unreadable_cost_is_an_error_not_a_pass(self):
        code, out = run_live({"odd@x": (True, "no cost line here")})
        self.assertEqual(code, 2, out)

    def test_missing_cli_is_an_error_not_a_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            proc = subprocess.run(
                [sys.executable, str(SCRIPT), "--live"],
                capture_output=True,
                text=True,
                env={**os.environ, "PATH": tmp},
            )
        self.assertEqual(proc.returncode, 2, proc.stdout)


if __name__ == "__main__":
    unittest.main()
