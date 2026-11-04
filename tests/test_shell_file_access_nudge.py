"""Behavioural tests for scripts/hooks/shell-file-access-nudge.sh."""

import json
import pathlib
import subprocess
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
HOOK = REPO_ROOT / "scripts" / "hooks" / "shell-file-access-nudge.sh"


def run_hook(command):
    proc = subprocess.run(
        [str(HOOK)],
        input=json.dumps({"tool_input": {"command": command}}),
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    return proc.returncode, proc.stdout


class TestNudges(unittest.TestCase):
    def assert_nudged(self, command, expected):
        code, out = run_hook(command)
        self.assertEqual(code, 0, command)
        self.assertTrue(out, f"expected a nudge for: {command!r}")
        output = json.loads(out)["hookSpecificOutput"]
        self.assertEqual(output["hookEventName"], "PreToolUse")
        self.assertNotIn("permissionDecision", output)
        self.assertIn(expected, output["additionalContext"])

    def test_compound_read(self):
        self.assert_nudged("cd foo && cat a.txt", "Use Read")
        self.assert_nudged("cd foo; sed -n 1,5p a.txt", "Use Read")

    def test_multi_file_read(self):
        self.assert_nudged("cat foo/a.txt foo/b.txt", "Use Read")

    def test_script_write(self):
        self.assert_nudged(
            "python3 - <<'E'\nimport pathlib\npathlib.Path('a').write_text('x')\nE", "Edit/Write"
        )
        self.assert_nudged("python3 -c \"open('a', 'w').write('x')\"", "Edit/Write")

    def test_in_place_edit(self):
        self.assert_nudged("sed -i '' s/a/b/ foo.py", "Edit/Write")
        self.assert_nudged("perl -pi -e 's/a/b/' foo.py", "Edit/Write")


class TestStaysQuiet(unittest.TestCase):
    def assert_quiet(self, command):
        code, out = run_hook(command)
        self.assertEqual(code, 0, command)
        self.assertEqual(out, "", f"unexpected nudge for: {command!r}")

    def test_simple_reads_load_rules(self):
        for command in ("cat a.txt", "head -2 a.txt", "sed -n 1,2p a.txt", "grep x a.txt"):
            self.assert_quiet(command)

    def test_unrelated_commands(self):
        for command in ("git status", "make test && git diff", "cat a.txt | wc -l"):
            self.assert_quiet(command)

    def test_python_without_a_write(self):
        self.assert_quiet("python3 -c \"print(open('a').read())\"")

    def test_scratch_paths(self):
        self.assert_quiet("python3 - <<'E'\nopen('/tmp/x', 'w').write('y')\nE")
        self.assert_quiet("cd /private/tmp/s && cat a b")
        self.assert_quiet("sed -i '' s/a/b/ /var/folders/x/y")

    def test_unparseable_payload_fails_open(self):
        proc = subprocess.run([str(HOOK)], input="not json", capture_output=True, text=True)
        self.assertEqual((proc.returncode, proc.stdout), (0, ""))


if __name__ == "__main__":
    unittest.main()
