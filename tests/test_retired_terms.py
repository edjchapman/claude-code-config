"""Tests for the retired-terms tripwire: no glossary "formerly" alias in a living doc."""

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
from lib.config_common import GenerationError  # noqa: E402
from lib.retired_terms import parse_retired_terms  # noqa: E402

GLOSSARY = """# Glossary

## Terms

- **Widget** — the thing this fixture ships. _Formerly described as "gadget
  factory", which confused everyone._
- **Install modes** — two of them. Concerns loading, not layers. _Formerly
  "old-style mode", renamed when the name went half-false._
- **Catalog** — no alias here.
"""


class AliasParser(unittest.TestCase):
    def test_recovers_both_aliases_declared_in_the_real_glossary(self) -> None:
        # The criterion that stops a silently-empty guard shipping green: one
        # of these wraps across a line break, the other says "described as".
        parsed = parse_retired_terms((REPO_ROOT / "CONTEXT.md").read_text())
        self.assertEqual(
            parsed, {"style enforcement": "Rule", "symlink-global mode": "Install modes"}
        )

    def test_bare_and_described_as_forms_across_line_breaks(self) -> None:
        self.assertEqual(
            parse_retired_terms(GLOSSARY),
            {"gadget factory": "Widget", "old-style mode": "Install modes"},
        )

    def test_an_entry_may_declare_several_aliases(self) -> None:
        text = '- **Thing** — it. _Formerly "alpha", and formerly described as "beta"._\n'
        self.assertEqual(parse_retired_terms(text), {"alpha": "Thing", "beta": "Thing"})

    def test_a_formerly_the_grammar_cannot_parse_is_an_error_not_a_silent_miss(self) -> None:
        text = "- **Thing** — it. _Formerly known as the doohickey._\n"
        with self.assertRaises(GenerationError) as caught:
            parse_retired_terms(text)
        self.assertIn("Thing", str(caught.exception))

    def test_no_aliases_is_an_empty_mapping(self) -> None:
        self.assertEqual(parse_retired_terms("- **Thing** — it.\n"), {})


class CheckOverATree(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        make_readme_fixture(self.root)
        self.generate()
        (self.root / "CONTEXT.md").write_text(GLOSSARY)
        stage(self.root)

    def generate(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(GENERATE), "--root", str(self.root), *args],
            capture_output=True,
            text=True,
        )

    def write(self, relative: str, content: str) -> None:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        stage(self.root)

    def assert_passes(self) -> None:
        result = self.generate("--check")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def assert_fails_at(self, location: str, term: str, entry: str) -> None:
        result = self.generate("--check")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn(location, result.stderr)
        self.assertIn(f'"{term}"', result.stderr)
        self.assertIn(f"**{entry}**", result.stderr)

    def test_clean_tree_passes(self) -> None:
        self.assert_passes()

    def test_the_glossarys_own_alias_declarations_do_not_fail(self) -> None:
        # CONTEXT.md is in the tree and holds every retired term by definition.
        self.assertIn("old-style mode", (self.root / "CONTEXT.md").read_text())
        self.assert_passes()

    def test_term_in_the_readme_fails_naming_file_line_and_entry(self) -> None:
        readme = self.root / "README.md"
        readme.write_text(readme.read_text() + "\nRuns in old-style mode only.\n")
        line = len(readme.read_text().splitlines())
        self.assert_fails_at(f"README.md:{line}", "old-style mode", "Install modes")

    def test_term_in_the_root_instruction_file_fails(self) -> None:
        self.write("CLAUDE.md", "# Rules\n\nThe gadget factory is here.\n")
        self.assert_fails_at("CLAUDE.md:3", "gadget factory", "Widget")

    def test_term_in_docs_fails_but_an_adr_is_exempt(self) -> None:
        self.write("docs/adr/0001-record.md", "# ADR\n\nIn old-style mode, hooks were global.\n")
        self.assert_passes()
        self.write("docs/guide.md", "# Guide\n\nIn old-style mode, hooks were global.\n")
        self.assert_fails_at("docs/guide.md:3", "old-style mode", "Install modes")

    def test_term_in_a_skill_or_an_agent_fails(self) -> None:
        for relative in ("skills/dom-skill/SKILL.md", "agents/alpha-agent.md"):
            with self.subTest(relative=relative):
                original = (self.root / relative).read_text()
                self.write(relative, original + "\nUse Old-Style Mode here.\n")
                line = len(original.splitlines()) + 2
                self.assert_fails_at(f"{relative}:{line}", "old-style mode", "Install modes")
                self.write(relative, original)

    def test_term_wrapped_across_a_line_break_fails_at_its_first_line(self) -> None:
        self.write(
            "docs/guide.md", "# Guide\n\nThe hooks run in old-style\nmode on this machine.\n"
        )
        self.assert_fails_at("docs/guide.md:3", "old-style mode", "Install modes")

    def test_a_longer_word_containing_the_term_does_not_fail(self) -> None:
        self.write("docs/guide.md", "# Guide\n\nThe not-old-style modes differ.\n")
        self.assert_passes()

    def test_script_header_is_scanned_but_script_body_is_not(self) -> None:
        self.write(
            "scripts/cli/report.sh",
            "#!/usr/bin/env bash\n# Summarize recent activity\n#\n# Usage: report.sh\n"
            'set -u\necho "old-style mode"\n',
        )
        self.assert_passes()
        self.write(
            "scripts/cli/report.sh",
            "#!/usr/bin/env bash\n# Summarize recent activity\n#\n"
            "# Works in old-style\n# mode too.\nset -u\n",
        )
        self.assert_fails_at("scripts/cli/report.sh:4", "old-style mode", "Install modes")

    def test_python_module_docstring_counts_as_a_script_header(self) -> None:
        self.write(
            "scripts/tool.py",
            '#!/usr/bin/env python3\n"""Do a thing.\n\nFor the gadget factory.\n"""\n\nX = 1\n',
        )
        self.assert_fails_at("scripts/tool.py:4", "gadget factory", "Widget")

    def test_every_violation_is_reported_in_one_run(self) -> None:
        self.write("docs/guide.md", "# Guide\n\nold-style mode\n\ngadget factory\n")
        result = self.generate("--check")
        self.assertEqual(result.returncode, 1)
        self.assertIn("docs/guide.md:3", result.stderr)
        self.assertIn("docs/guide.md:5", result.stderr)

    def test_a_tree_without_a_glossary_is_not_checked(self) -> None:
        (self.root / "CONTEXT.md").unlink()
        self.write("docs/guide.md", "# Guide\n\nold-style mode\n")
        self.assert_passes()


if __name__ == "__main__":
    unittest.main()
