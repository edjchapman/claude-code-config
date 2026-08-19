"""Fixture-repo builders shared by the generate.py CLI tests.

Each `_write_*` helper lays down one catalog family; `make_readme_fixture`
composes them into the full fixture root the readme-target tests run
against. Discovery (`python3 -m unittest discover -s tests`) puts this
directory on sys.path, so the tests import this module by its bare name.
"""

from __future__ import annotations

import json
from pathlib import Path

HOOK_ENTRY = [
    {
        "hooks": [
            {
                "type": "command",
                "command": "${CLAUDE_PLUGIN_DIR:-fallback}/scripts/hooks/session-context.sh",
            }
        ]
    }
]

README_REGIONS = [
    "counts",
    "agents",
    "workflow-skills",
    "domain-skills",
    "rules",
    "hooks",
    "settings-templates",
    "mcp-templates",
    "cli-scripts",
    "repo-tree",
]


def canonical(obj: dict) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=False) + "\n"


def region_markers(name: str) -> str:
    return f"<!-- BEGIN GENERATED: {name} -->\nstale placeholder\n<!-- END GENERATED: {name} -->"


def make_fixture(root: Path, settings_hooks: dict, source_hooks: dict) -> None:
    """Write a minimal repo root: settings.json + hooks/hooks.json."""
    (root / "hooks").mkdir()
    (root / "hooks" / "hooks.json").write_text(
        canonical({"$schema": "https://example.invalid/schema.json", "hooks": source_hooks})
    )
    (root / "settings.json").write_text(
        canonical(
            {
                "$schema": "https://example.invalid/schema.json",
                "attribution": {"commit": "", "pr": "", "sessionUrl": False},
                "hooks": settings_hooks,
                "tui": "fullscreen",
                "autoMemoryEnabled": False,
            }
        )
    )


def _write_agents(root: Path) -> None:
    (root / "agents").mkdir()
    (root / "agents" / "alpha-agent.md").write_text(
        "---\nname: alpha-agent\ndescription: >-\n  Investigates alpha problems.\n---\nbody\n"
    )
    (root / "agents" / "beta-agent.md").write_text(
        "---\nname: beta-agent\ndescription: Handles beta work.\nmodel: sonnet\n---\nbody\n"
    )


def _write_skills(root: Path) -> None:
    skills = {
        "dom-skill": "---\nname: dom-skill\ndescription: Use when editing dom things.\n---\n",
        "flow-skill": (
            '---\nname: flow-skill\ndescription: Flow the flow.\nargument-hint: "<what>"\n---\n'
        ),
        "solo-skill": (
            '---\nname: solo-skill\ndescription: Solo only.\nargument-hint: "<msg>"\n'
            "disable-model-invocation: true\n---\n"
        ),
        "standup": (
            "---\nname: standup\ndescription: Prepare a standup summary.\n"
            'argument-hint: "[p]"\n---\n'
        ),
    }
    for name, content in skills.items():
        (root / "skills" / name).mkdir(parents=True)
        (root / "skills" / name / "SKILL.md").write_text(content + "body\n")


def _write_rules(root: Path) -> None:
    (root / "rules").mkdir()
    (root / "rules" / "demo-style.md").write_text(
        '---\npaths:\n  - "**/*.demo"\n---\n\n# Demo Rules\n\n## Naming\n\n## Errors\n'
    )


def _write_templates(root: Path) -> None:
    (root / "settings-templates").mkdir()
    (root / "settings-templates" / "base.json").write_text(
        canonical({"_source": "base", "_description": "Git and file operations", "permissions": {}})
    )
    (root / "mcp-templates").mkdir()
    (root / "mcp-templates" / "base.json").write_text(
        canonical({"_source": "base", "mcpServers": {}})
    )
    (root / "mcp-templates" / "python.json").write_text(
        canonical({"_source": "python", "mcpServers": {"sqlite": {"$fragment": "sqlite"}}})
    )


def _write_scripts(root: Path) -> None:
    hooks_dir = root / "scripts" / "hooks"
    hooks_dir.mkdir(parents=True)
    (hooks_dir / "one.sh").write_text("#!/usr/bin/env bash\n# Emits session context\nset -u\n")
    (hooks_dir / "two.sh").write_text(
        "#!/usr/bin/env bash\n# Restores state after compaction\nset -u\n"
    )
    cli_dir = root / "scripts" / "cli"
    cli_dir.mkdir(parents=True)
    (cli_dir / "report.sh").write_text(
        "#!/usr/bin/env bash\n# Summarize recent activity\n#\n# Usage: report.sh\nset -u\n"
    )


def _write_readme(root: Path) -> None:
    regions = "\n\n".join(region_markers(name) for name in README_REGIONS)
    (root / "README.md").write_text(
        "# Fixture Readme\n\nHAND-WRITTEN-TOP\n\n"
        + regions
        + "\n\n"
        + '### "I want to…" lookup\n\n'
        + "| I want to... | Use |\n| --- | --- |\n| Flow it | `/flow-skill` |\n\n"
        + "HAND-WRITTEN-BOTTOM\n"
    )


def make_readme_fixture(root: Path) -> None:
    """Write a full fixture repo: every catalog source plus a marked-up README."""
    make_fixture(
        root,
        settings_hooks={},
        source_hooks={
            "SessionStart": [
                {"hooks": [{"type": "command", "command": "${X:-y}/scripts/hooks/one.sh"}]}
            ],
            "PostToolUse": [
                {
                    "matcher": "Write|Edit",
                    "hooks": [{"type": "command", "command": "${X:-y}/scripts/hooks/one.sh"}],
                }
            ],
            "PostCompact": [
                {"hooks": [{"type": "command", "command": "${X:-y}/scripts/hooks/two.sh"}]}
            ],
        },
    )
    _write_agents(root)
    _write_skills(root)
    _write_rules(root)
    _write_templates(root)
    _write_scripts(root)
    _write_readme(root)
