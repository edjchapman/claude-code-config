"""Tests for tooling/scripts/check_anchors.py — the GFM heading slugifier and its CLI."""

import pathlib
import subprocess
import sys
import tempfile
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "tooling" / "scripts" / "check_anchors.py"

sys.path.insert(0, str(SCRIPT.parent))
import check_anchors  # noqa: E402

# Heading text as HEADING_RE captures it (no leading `#`s) -> expected slug.
SLUG_CORPUS = {
    "Plain Heading": "plain-heading",
    "Heading_With_Underscores": "heading_with_underscores",
    "snake_case_identifier": "snake_case_identifier",
    "CLAUDE_PLUGIN_ROOT": "claude_plugin_root",
    "The `parse_frontmatter` helper": "the-parse_frontmatter-helper",
    "*Emphasis* in a heading": "emphasis-in-a-heading",
    "**Bold** in a heading": "bold-in-a-heading",
    "Inline `code` span": "inline-code-span",
    "Mixed **bold**, *em* and `code`": "mixed-bold-em-and-code",
    "What's new? (v2.0)": "whats-new-v20",
    "Two  spaces": "two--spaces",
    "kebab-case-already": "kebab-case-already",
    "_": "_",
    "*": "",
}


def run_checker(files):
    """Run the checker over {relative path: content} staged in a throwaway git repo."""
    with tempfile.TemporaryDirectory() as tmp:
        root = pathlib.Path(tmp)
        for rel, content in files.items():
            (root / rel).write_text(content)
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        subprocess.run(["git", "add", "-A"], cwd=root, check=True)
        proc = subprocess.run(
            [sys.executable, str(SCRIPT)], cwd=root, capture_output=True, text=True
        )
    return proc.returncode, proc.stdout


class TestSlugifyGfm(unittest.TestCase):
    def test_corpus(self):
        for heading, expected in SLUG_CORPUS.items():
            with self.subTest(heading=heading):
                self.assertEqual(check_anchors.slugify_gfm(heading), expected)

    def test_formatting_characters_never_reach_a_slug(self):
        for heading in SLUG_CORPUS:
            with self.subTest(heading=heading):
                slug = check_anchors.slugify_gfm(heading)
                self.assertNotIn("*", slug)
                self.assertNotIn("`", slug)


class TestCheckerCli(unittest.TestCase):
    DOC = "# Doc\n\n## Heading_With_Underscores\n\n## snake_case_identifier\n"

    def test_links_to_underscore_headings_resolve(self):
        code, out = run_checker(
            {
                "doc.md": self.DOC,
                "index.md": (
                    "# Index\n\n"
                    "[a](./doc.md#heading_with_underscores)\n"
                    "[b](./doc.md#snake_case_identifier)\n"
                ),
            }
        )
        self.assertEqual(code, 0, out)
        self.assertIn("all 2 anchor fragments resolve", out)

    def test_a_link_to_a_missing_heading_still_fails(self):
        code, out = run_checker(
            {
                "doc.md": self.DOC,
                "index.md": "# Index\n\n[a](./doc.md#snakecaseidentifier)\n",
            }
        )
        self.assertEqual(code, 1, out)
        self.assertIn("doc.md#snakecaseidentifier", out)


if __name__ == "__main__":
    unittest.main()
