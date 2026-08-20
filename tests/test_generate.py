"""CLI tests for scripts/generate.py (ADR-0001).

The generator's CLI is its interface and therefore the test surface: every
test builds a fixture repo root, invokes the CLI as a subprocess, and asserts
on exit codes and resulting file bytes — never on internals.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from fixtures import HOOK_ENTRY, canonical, make_fixture, make_readme_fixture

REPO_ROOT = Path(__file__).resolve().parent.parent
GENERATE = REPO_ROOT / "scripts" / "generate.py"


def run_generate(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(GENERATE), "--root", str(root), *args],
        capture_output=True,
        text=True,
    )


def extract_region(text: str, name: str) -> str:
    begin = f"<!-- BEGIN GENERATED: {name} -->"
    end = f"<!-- END GENERATED: {name} -->"
    return text.split(begin, 1)[1].split(end, 1)[0]


class ReadmeCatalogs(unittest.TestCase):
    """The 'readme' target renders every catalog region from disk (issue #112)."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)
        make_readme_fixture(self.root)

    def readme(self) -> str:
        return (self.root / "README.md").read_text()

    def test_check_fails_stale_then_passes_after_write(self) -> None:
        check = run_generate(self.root, "--check")
        self.assertEqual(check.returncode, 1)
        self.assertIn("README.md", check.stdout + check.stderr)
        write = run_generate(self.root)
        self.assertEqual(write.returncode, 0, write.stdout + write.stderr)
        recheck = run_generate(self.root, "--check")
        self.assertEqual(recheck.returncode, 0, recheck.stdout + recheck.stderr)

    def test_catalogs_render_from_disk(self) -> None:
        run_generate(self.root, "--only", "readme")
        text = self.readme()
        self.assertIn("`@alpha-agent`", extract_region(text, "agents"))
        self.assertIn("Investigates alpha problems.", text)
        hooks = extract_region(text, "hooks")
        self.assertIn("PostCompact", hooks)
        self.assertIn("Restores state after compaction", hooks)
        self.assertIn("PostToolUse (Write\\|Edit)", hooks)
        self.assertIn("`2 specialist agents`", extract_region(text, "counts"))
        self.assertIn("`4 skills`", extract_region(text, "counts"))
        self.assertIn("`3 lifecycle hooks`", extract_region(text, "counts"))
        tree = extract_region(text, "repo-tree")
        self.assertIn("one.sh", tree)
        self.assertIn("two.sh", tree)
        self.assertIn("report.sh", tree)

    def test_who_can_invoke_is_derived_from_frontmatter(self) -> None:
        run_generate(self.root, "--only", "readme")
        workflow = extract_region(self.readme(), "workflow-skills")
        flow_row = next(line for line in workflow.splitlines() if "`/flow-skill`" in line)
        solo_row = next(line for line in workflow.splitlines() if "`/solo-skill`" in line)
        standup_row = next(line for line in workflow.splitlines() if "`/standup`" in line)
        self.assertIn("you or Claude", flow_row)
        self.assertIn("you only", solo_row)
        self.assertIn("you, Claude, or a schedule", standup_row)

    def test_skills_split_into_workflow_and_domain(self) -> None:
        run_generate(self.root, "--only", "readme")
        text = self.readme()
        self.assertIn("dom-skill", extract_region(text, "domain-skills"))
        self.assertNotIn("dom-skill", extract_region(text, "workflow-skills"))
        self.assertNotIn("flow-skill", extract_region(text, "domain-skills"))

    def test_hand_written_prose_is_preserved(self) -> None:
        run_generate(self.root, "--only", "readme")
        text = self.readme()
        self.assertIn("HAND-WRITTEN-TOP", text)
        self.assertIn("HAND-WRITTEN-BOTTOM", text)
        self.assertIn("| Flow it | `/flow-skill` |", text)

    def test_second_run_is_a_byte_level_noop(self) -> None:
        run_generate(self.root, "--only", "readme")
        first = (self.root / "README.md").read_bytes()
        second = run_generate(self.root, "--only", "readme")
        self.assertEqual(second.returncode, 0)
        self.assertEqual((self.root / "README.md").read_bytes(), first)

    def test_uncurated_skill_warns_without_failing(self) -> None:
        result = run_generate(self.root, "--only", "readme")
        self.assertEqual(result.returncode, 0)
        self.assertIn("dom-skill", result.stderr)
        self.assertIn("cheat-sheet", result.stderr)
        self.assertNotIn("'flow-skill'", result.stderr)
        check = run_generate(self.root, "--check", "--only", "readme")
        self.assertEqual(check.returncode, 0)

    def test_missing_marker_pair_is_a_named_error(self) -> None:
        readme = self.readme().replace("<!-- BEGIN GENERATED: agents -->", "")
        (self.root / "README.md").write_text(readme)
        result = run_generate(self.root, "--only", "readme")
        self.assertEqual(result.returncode, 1)
        self.assertIn("agents", result.stderr)

    def test_scheduled_skill_disabling_model_invocation_is_an_error(self) -> None:
        (self.root / "skills" / "standup" / "SKILL.md").write_text(
            "---\nname: standup\ndescription: Prepare a standup summary.\n"
            "disable-model-invocation: true\n---\nbody\n"
        )
        result = run_generate(self.root, "--check", "--only", "readme")
        self.assertEqual(result.returncode, 1)
        self.assertIn("scheduling invariant", result.stderr)
        self.assertIn("standup", result.stderr)

    def test_user_only_skill_losing_its_flag_is_an_error(self) -> None:
        """The other half of the scheduling invariant (issue #115)."""
        (self.root / "skills" / "status").mkdir(parents=True)
        (self.root / "skills" / "status" / "SKILL.md").write_text(
            "---\nname: status\ndescription: Log a status line.\n---\nbody\n"
        )
        result = run_generate(self.root, "--check", "--only", "readme")
        self.assertEqual(result.returncode, 1)
        self.assertIn("scheduling invariant", result.stderr)
        self.assertIn("status", result.stderr)

    def test_unrecognised_invocation_flag_is_an_error(self) -> None:
        (self.root / "skills" / "solo-skill" / "SKILL.md").write_text(
            "---\nname: solo-skill\ndescription: Solo only.\n"
            "disable-model-invocation: yes\n---\nbody\n"
        )
        result = run_generate(self.root, "--only", "readme")
        self.assertEqual(result.returncode, 1)
        self.assertIn("disable-model-invocation", result.stderr)

    def test_template_without_description_is_an_error(self) -> None:
        (self.root / "settings-templates" / "base.json").write_text(
            canonical({"_source": "base", "permissions": {}})
        )
        result = run_generate(self.root, "--only", "readme")
        self.assertEqual(result.returncode, 1)
        self.assertIn("_description", result.stderr)

    def test_full_run_updates_both_targets(self) -> None:
        write = run_generate(self.root)
        self.assertEqual(write.returncode, 0)
        settings = json.loads((self.root / "settings.json").read_text())
        self.assertIn("PostCompact", settings["hooks"])
        self.assertIn("PostCompact", extract_region(self.readme(), "hooks"))


class ArchitectureReference(unittest.TestCase):
    """The 'architecture' target renders docs/architecture.md (issue #114)."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)
        make_readme_fixture(self.root)

    def architecture(self) -> str:
        return (self.root / "docs" / "architecture.md").read_text()

    def test_check_fails_stale_then_passes_after_write(self) -> None:
        check = run_generate(self.root, "--check", "--only", "architecture")
        self.assertEqual(check.returncode, 1)
        self.assertIn("architecture.md", check.stdout + check.stderr)
        write = run_generate(self.root, "--only", "architecture")
        self.assertEqual(write.returncode, 0, write.stdout + write.stderr)
        recheck = run_generate(self.root, "--check", "--only", "architecture")
        self.assertEqual(recheck.returncode, 0, recheck.stdout + recheck.stderr)

    def test_second_run_is_a_byte_level_noop(self) -> None:
        run_generate(self.root, "--only", "architecture")
        first = (self.root / "docs" / "architecture.md").read_bytes()
        second = run_generate(self.root, "--only", "architecture")
        self.assertEqual(second.returncode, 0)
        self.assertEqual((self.root / "docs" / "architecture.md").read_bytes(), first)

    def test_hand_written_prose_is_preserved(self) -> None:
        run_generate(self.root, "--only", "architecture")
        text = self.architecture()
        self.assertIn("ARCH-HAND-WRITTEN-TOP", text)
        self.assertIn("ARCH-HAND-WRITTEN-BOTTOM", text)

    def test_hook_rationale_is_projected_from_the_script_header(self) -> None:
        run_generate(self.root, "--only", "architecture")
        hooks = extract_region(self.architecture(), "arch-hooks")
        self.assertIn("it closes the loop pre-compaction only half-opened", hooks)
        self.assertNotIn("must not be projected", hooks)
        one = next(line for line in hooks.splitlines() if "one.sh" in line)
        self.assertNotIn("_Why:_", one)

    def test_a_wired_event_leaves_the_unwired_table(self) -> None:
        """The class of stale claim T4 exists to kill: PostCompact is wired here."""
        run_generate(self.root, "--only", "architecture")
        unwired = extract_region(self.architecture(), "arch-unwired-events")
        self.assertNotIn("`PostCompact`", unwired)
        self.assertIn("`SubagentStart`", unwired)
        self.assertIn("this repo wires 3 of them", unwired)

    def test_a_set_settings_key_leaves_the_unset_list(self) -> None:
        run_generate(self.root, "--only", "architecture")
        text = self.architecture()
        self.assertIn("`autoMemoryEnabled`", extract_region(text, "arch-settings-keys"))
        self.assertNotIn("`autoMemoryEnabled`", extract_region(text, "arch-unset-settings-keys"))
        self.assertIn("`fastMode`", extract_region(text, "arch-unset-settings-keys"))

    def test_verbatim_globs_survive_into_the_bullet_lists(self) -> None:
        """Unescaped `*` would render as emphasis and eat the glob."""
        run_generate(self.root, "--only", "architecture")
        skills = extract_region(self.architecture(), "arch-skills")
        self.assertIn("test\\_\\*, \\*.spec.\\*", skills)

    def test_settings_key_without_a_gloss_is_an_error(self) -> None:
        settings = json.loads((self.root / "settings.json").read_text())
        settings["someInventedKey"] = True
        (self.root / "settings.json").write_text(canonical(settings))
        result = run_generate(self.root, "--only", "architecture")
        self.assertEqual(result.returncode, 1)
        self.assertIn("someInventedKey", result.stderr)

    def test_skill_markers_are_derived_from_frontmatter(self) -> None:
        run_generate(self.root, "--only", "architecture")
        skills = extract_region(self.architecture(), "arch-skills")
        solo = next(line for line in skills.splitlines() if "`/solo-skill`" in line)
        standup = next(line for line in skills.splitlines() if "`/standup`" in line)
        self.assertIn("**User-only.**", solo)
        self.assertIn("**Schedulable**", standup)
        self.assertIn("issue #51", standup)

    def test_full_run_updates_every_destination(self) -> None:
        result = run_generate(self.root)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("`report.sh`", extract_region(self.architecture(), "arch-cli-scripts"))
        self.assertIn("`demo-style`", extract_region(self.architecture(), "arch-rules"))


class StaleHooksBlock(unittest.TestCase):
    """A settings.json hooks block that lags hooks/hooks.json."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)
        make_fixture(
            self.root,
            settings_hooks={"SessionStart": HOOK_ENTRY},
            source_hooks={"SessionStart": HOOK_ENTRY, "SessionEnd": HOOK_ENTRY},
        )

    def test_check_fails_naming_the_stale_file(self) -> None:
        result = run_generate(self.root, "--check", "--only", "settings-hooks")
        self.assertEqual(result.returncode, 1)
        self.assertIn("settings.json", result.stdout + result.stderr)

    def test_write_mode_fixes_then_check_passes(self) -> None:
        write = run_generate(self.root, "--only", "settings-hooks")
        self.assertEqual(write.returncode, 0)
        updated = json.loads((self.root / "settings.json").read_text())
        self.assertIn("SessionEnd", updated["hooks"])
        check = run_generate(self.root, "--check", "--only", "settings-hooks")
        self.assertEqual(check.returncode, 0, check.stdout + check.stderr)


class PreservationAndIdempotency(unittest.TestCase):
    """Non-hooks content survives byte-for-byte; regeneration converges."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)
        make_fixture(
            self.root,
            settings_hooks={},
            source_hooks={"SessionStart": HOOK_ENTRY},
        )

    def test_only_the_hooks_block_changes(self) -> None:
        before = json.loads((self.root / "settings.json").read_text())
        run_generate(self.root, "--only", "settings-hooks")
        after_text = (self.root / "settings.json").read_text()
        after = json.loads(after_text)
        self.assertEqual(after["hooks"], {"SessionStart": HOOK_ENTRY})
        before["hooks"] = {"SessionStart": HOOK_ENTRY}
        self.assertEqual(after_text, canonical(before))

    def test_second_run_is_a_byte_level_noop(self) -> None:
        run_generate(self.root, "--only", "settings-hooks")
        first = (self.root / "settings.json").read_bytes()
        second_run = run_generate(self.root, "--only", "settings-hooks")
        self.assertEqual(second_run.returncode, 0)
        self.assertIn("up to date", second_run.stdout)
        self.assertEqual((self.root / "settings.json").read_bytes(), first)

    def test_in_sync_fixture_passes_check_untouched(self) -> None:
        run_generate(self.root, "--only", "settings-hooks")
        before = (self.root / "settings.json").read_bytes()
        check = run_generate(self.root, "--check", "--only", "settings-hooks")
        self.assertEqual(check.returncode, 0)
        self.assertEqual((self.root / "settings.json").read_bytes(), before)


class CliContract(unittest.TestCase):
    """Interface details a caller (pre-commit, CI, a human) relies on."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)

    def test_only_selects_a_known_target(self) -> None:
        make_fixture(self.root, settings_hooks={}, source_hooks={"SessionStart": HOOK_ENTRY})
        result = run_generate(self.root, "--only", "settings-hooks")
        self.assertEqual(result.returncode, 0)
        updated = json.loads((self.root / "settings.json").read_text())
        self.assertIn("SessionStart", updated["hooks"])

    def test_unknown_target_is_rejected(self) -> None:
        result = run_generate(self.root, "--only", "no-such-target")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("no-such-target", result.stderr)

    def test_missing_source_fails_with_a_named_error(self) -> None:
        (self.root / "settings.json").write_text(canonical({"hooks": {}}))
        result = run_generate(self.root, "--check")
        self.assertEqual(result.returncode, 1)
        self.assertIn("hooks.json", result.stderr)


if __name__ == "__main__":
    unittest.main()
