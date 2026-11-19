"""Tests for parse_frontmatter — malformed blocks fail at parse time (issue #122)."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from fixtures import make_readme_fixture, stage

REPO_ROOT = Path(__file__).resolve().parent.parent
GENERATE = REPO_ROOT / "scripts" / "generate.py"

sys.path.insert(0, str(REPO_ROOT / "scripts"))
from lib.config_common import GenerationError, parse_frontmatter  # noqa: E402


class ParseFrontmatter(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "sample.md"

    def parse(self, frontmatter: str) -> dict:
        self.path.write_text(f"---\n{frontmatter}---\nbody\n")
        return parse_frontmatter(self.path)

    def assert_rejected(self, frontmatter: str, key: str) -> None:
        with self.assertRaises(GenerationError) as caught:
            self.parse(frontmatter)
        message = str(caught.exception)
        self.assertIn(str(self.path), message)
        self.assertIn(f"`{key}:`", message)

    def test_indented_key_is_an_error_naming_file_and_key(self) -> None:
        self.assert_rejected(
            "name: foo\n  descriptiom: typo\ndescription: real one\n", "descriptiom"
        )

    def test_tab_indented_key_is_an_error(self) -> None:
        self.assert_rejected("name: foo\n\tmodel: sonnet\n", "model")

    def test_key_nested_under_a_bare_key_is_an_error(self) -> None:
        self.assert_rejected("name: foo\nmetadata:\n  kind: nested\n", "kind")

    def test_duplicate_key_is_an_error_naming_file_and_key(self) -> None:
        self.assert_rejected("description: FIRST\nname: foo\ndescription: SECOND\n", "description")

    def test_block_scalar_continuation_with_a_colon_is_one_string(self) -> None:
        for indicator in (">", ">-", "|", "|-"):
            with self.subTest(indicator=indicator):
                parsed = self.parse(
                    f"name: foo\ndescription: {indicator}\n  Does a thing.\n"
                    "  Use when: the thing needs doing.\n  note: still the description\n"
                    "model: sonnet\n"
                )
                self.assertEqual(
                    parsed["description"],
                    "Does a thing. Use when: the thing needs doing. note: still the description",
                )
                self.assertEqual(parsed["model"], "sonnet")

    def test_list_under_a_bare_key_parses_to_a_list(self) -> None:
        parsed = self.parse('name: foo\npaths:\n  - "**/*.py"\n  - docs/*.md\nmodel: sonnet\n')
        self.assertEqual(parsed["paths"], ["**/*.py", "docs/*.md"])
        self.assertEqual(parsed["model"], "sonnet")

    def test_indented_prose_that_is_not_key_shaped_is_still_ignored(self) -> None:
        parsed = self.parse("name: foo\n  see https://example.invalid/page\n  two words: here\n")
        self.assertEqual(parsed, {"name": "foo"})

    def test_plain_scalars_parse_unchanged(self) -> None:
        parsed = self.parse('name: foo\ndescription: "Quoted: with a colon"\n# a comment\n')
        self.assertEqual(parsed, {"name": "foo", "description": "Quoted: with a colon"})


class GeneratorSurfacesTheError(unittest.TestCase):
    """A consumer reports the parse error instead of rendering from half a block."""

    def test_generate_fails_on_an_indented_key(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_readme_fixture(root)
            (root / "agents" / "beta-agent.md").write_text(
                "---\nname: beta-agent\n  modle: sonnet\ndescription: Beta work.\n---\nbody\n"
            )
            stage(root)
            result = subprocess.run(
                [sys.executable, str(GENERATE), "--root", str(root)],
                capture_output=True,
                text=True,
            )
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("beta-agent.md", result.stderr)
        self.assertIn("`modle:`", result.stderr)


if __name__ == "__main__":
    unittest.main()
