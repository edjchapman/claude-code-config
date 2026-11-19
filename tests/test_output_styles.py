"""Tests for output styles as a generated primitive (issue #149)."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from fixtures import canonical, make_readme_fixture, stage

REPO_ROOT = Path(__file__).resolve().parent.parent
GENERATE = REPO_ROOT / "scripts" / "generate.py"

TIDY_DESCRIPTION = "Tidy output, in short_lines — never *walls*."


def extract_region(text: str, name: str) -> str:
    begin = f"<!-- BEGIN GENERATED: {name} -->"
    end = f"<!-- END GENERATED: {name} -->"
    return text.split(begin, 1)[1].split(end, 1)[0]


class OutputStyleCase(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        make_readme_fixture(self.root)

    def generate(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(GENERATE), "--root", str(self.root), *args],
            capture_output=True,
            text=True,
        )

    def write_style(self, file_name: str, frontmatter: str) -> None:
        (self.root / "output-styles" / file_name).write_text(f"---\n{frontmatter}---\n\n# Body\n")
        stage(self.root)

    def set_output_style(self, value: str | None) -> None:
        path = self.root / "settings.json"
        settings = json.loads(path.read_text())
        settings.pop("outputStyle", None)
        if value is not None:
            settings["outputStyle"] = value
        path.write_text(canonical(settings))
        stage(self.root)

    def region(self, relative: str, name: str) -> str:
        return extract_region((self.root / relative).read_text(), name)


class Catalogs(OutputStyleCase):
    def test_shipped_style_renders_in_counts_readme_and_architecture(self) -> None:
        result = self.generate()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("`1 output style`", self.region("README.md", "counts"))
        readme = self.region("README.md", "output-styles")
        self.assertIn("`Tidy`", readme)
        self.assertIn("`output-styles/tidy.md`", readme)
        # Verbatim frontmatter survives unparsed as emphasis.
        self.assertIn("Tidy output, in short\\_lines — never \\*walls\\*.", readme)
        architecture = self.region("docs/architecture.md", "arch-output-styles")
        self.assertIn("`Tidy`", architecture)
        self.assertIn("Tidy output, in short\\_lines — never \\*walls\\*.", architecture)

    def test_a_second_style_appears_everywhere_by_regeneration_alone(self) -> None:
        self.generate()
        self.write_style("loud.md", "name: Loud\ndescription: Everything in capitals.\n")
        result = self.generate()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("`2 output styles`", self.region("README.md", "counts"))
        for relative, name in (
            ("README.md", "output-styles"),
            ("docs/architecture.md", "arch-output-styles"),
        ):
            with self.subTest(region=name):
                region = self.region(relative, name)
                self.assertIn("`Loud`", region)
                self.assertIn("Everything in capitals.", region)
                self.assertIn("`Tidy`", region)

    def test_an_untracked_style_stays_out_of_the_catalogs(self) -> None:
        (self.root / "output-styles" / "local.md").write_text(
            "---\nname: Local\ndescription: Mine only.\n---\n"
        )
        self.generate()
        self.assertNotIn("Local", self.region("README.md", "output-styles"))

    def test_style_without_a_description_fails_naming_the_file(self) -> None:
        self.write_style("bare.md", "name: Bare\n")
        result = self.generate()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("description", result.stderr)
        self.assertIn("bare.md", result.stderr)

    def test_a_style_with_no_name_is_listed_under_its_file_name(self) -> None:
        self.write_style("plain.md", "description: No name key at all.\n")
        self.generate()
        self.assertIn("`plain`", self.region("README.md", "output-styles"))


class SettingNamesAShippedStyle(OutputStyleCase):
    """The managed outputStyle value must be the name of a style this repo ships."""

    def assert_check_fails_naming(self, *expected: str) -> None:
        result = self.generate("--check")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("outputStyle", result.stderr)
        for text in expected:
            self.assertIn(text, result.stderr)

    def test_matching_value_passes(self) -> None:
        self.set_output_style("Tidy")
        self.generate()
        result = self.generate("--check")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_value_no_style_declares_fails_naming_both_sides(self) -> None:
        self.set_output_style("Tidy")
        self.generate()
        self.set_output_style("Neat")
        self.assert_check_fails_naming("'Neat'", "'Tidy'")

    def test_renaming_the_style_without_the_setting_fails_the_same_way(self) -> None:
        self.set_output_style("Tidy")
        self.generate()
        self.write_style("tidy.md", f"name: Neat\ndescription: {TIDY_DESCRIPTION}\n")
        self.assert_check_fails_naming("'Tidy'", "'Neat'")

    def test_the_comparison_is_case_sensitive(self) -> None:
        # Also the file-name case: tidy.md sets `name: Tidy`, so its stem no longer matches.
        self.set_output_style("tidy")
        self.assert_check_fails_naming("'tidy'", "'Tidy'")

    def test_a_style_with_no_name_is_matched_by_its_file_name(self) -> None:
        self.write_style("plain.md", "description: No name key at all.\n")
        self.set_output_style("plain")
        self.generate()
        result = self.generate("--check")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_no_setting_is_no_claim(self) -> None:
        self.set_output_style(None)
        self.generate()
        result = self.generate("--check")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
