"""Region content builders for generate.py's 'readme' target (issue #112).

Each builder renders one README generated region from the primitives on
disk (read by primitives.py), so the catalogs cannot disagree with what
ships: descriptions render verbatim from their canonical source, and
derived columns (who-can-invoke, the workflow/domain split, MCP server
lists, counts) are computed, never hand-written. The repository tree's
hook and CLI branches are enumerated from disk; its fixed skeleton is
curated in _TREE below — this module is that region's source, so skeleton
edits belong here.

Every region is wrapped in prettier-ignore fences: prettier re-pads
markdown tables, and the generator — not prettier — owns region formatting
(the same reasoning that put settings.json in .prettierignore).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import NamedTuple

from lib import primitives
from lib.catalog_render import details_body, fence, table
from lib.config_common import GenerationError
from lib.primitives import Skill


class Catalog(NamedTuple):
    """One plain table region: its badge-count label, headers, and rows."""

    label: str
    headers: list[str]
    rows: list[list[str]]


# scripts/hooks/ entries whose purpose no hooks.json event explains.
EXTRA_HOOK_NOTES = {
    "statusline.sh": "settings.json statusLine.command",
    "check-duplicates.sh": "CI-only (validate-config.yml)",
    "lib": "shared helpers sourced by the hook scripts",
}

CHEATSHEET_HEADING = '### "I want to…" lookup'

_TREE = """\
claude-code-config/
├── agents/                  # Agent definitions (markdown)
├── skills/                  # Domain + workflow skills (skills/<name>/SKILL.md)
├── rules/                   # Path-scoped code style rules (markdown)
├── settings-templates/      # Permission templates (JSON)
├── mcp-templates/           # MCP server templates (JSON)
├── hooks/
│   └── hooks.json           # Hook definitions — source of truth (ADR-0001)
├── settings.json            # Plugin config; 'hooks' key generated from hooks/hooks.json
├── tooling/                 # Vendored project hard-tooling payload (--tooling)
└── scripts/
    ├── setup-global.sh      # One-time machine setup
    ├── setup-project.sh     # Per-project setup (+ --tooling)
    ├── install-tooling.sh   # Vendors tooling/ into a project (--tooling)
    ├── install-mkdocs-style.sh  # Installs/updates the shared MkDocs style layer
    ├── merge-settings.py    # Permission template merger
    ├── merge-mcp.py         # MCP template merger
    ├── generate.py          # Regenerates generated regions (ADR-0001)
    ├── check-context-budget.py  # CI: always-loaded context ≤ byte budget
    ├── check-agent-frontmatter.py  # CI: agent frontmatter contract holds
    ├── check-settings-keys.py  # pre-commit+CI: settings.json keys allowlisted
    ├── lib/                 # Shared Python helpers (primitives, catalog renderers)
    ├── hooks/               # Hook scripts (annotated with their trigger)
{hook_lines}
    └── cli/                 # Headless CLI automation scripts
{cli_lines}"""


def _invoke_column(skill: Skill) -> str:
    if skill.user_only:
        return "you only"
    if skill.scheduled:
        return "you, Claude, or a schedule"
    return "you or Claude"


def _branch_lines(indent: str, items: list[tuple[str, str]]) -> str:
    width = max(len(display) for display, _ in items)
    lines = []
    for i, (display, note) in enumerate(items):
        connector = "└──" if i == len(items) - 1 else "├──"
        name = display.ljust(width) if note else display
        suffix = f"  # {note}" if note else ""
        lines.append(f"{indent}{connector} {name}{suffix}")
    return "\n".join(lines)


def _tree(root: Path, hook_notes: dict[str, str]) -> str:
    notes = {**hook_notes, **EXTRA_HOOK_NOTES}
    hooks_dir = root / "scripts" / "hooks"
    hook_items = [(p.name, notes.get(p.name, "")) for p in sorted(hooks_dir.glob("*.sh"))]
    if (hooks_dir / "lib").is_dir():
        hook_items.append(("lib/", notes["lib"]))
    if not hook_items:
        raise GenerationError(f"no hook scripts found under {hooks_dir}")
    cli_items = [(p.name, "") for p in sorted((root / "scripts" / "cli").glob("*.sh"))]
    if not cli_items:
        raise GenerationError(f"no CLI scripts found under {root / 'scripts' / 'cli'}")
    return _TREE.format(
        hook_lines=_branch_lines("    │   ", hook_items),
        cli_lines=_branch_lines("        ", cli_items),
    )


def _catalog_tables(root: Path, skills: list[Skill]) -> dict[str, Catalog]:
    """{region name: Catalog} for the plain table regions."""
    workflow = [[f"`/{s.name}`", s.description, _invoke_column(s)] for s in skills if s.workflow]
    domain = [[f"`{s.name}`", s.description] for s in skills if not s.workflow]
    agents = [[f"`@{a.name}`", a.description, f"`{a.model}`"] for a in primitives.agents(root)]
    rules = [
        [f"`{r.name}`", ", ".join(f"`{p}`" for p in r.paths), ", ".join(r.headings)]
        for r in primitives.rules(root)
    ]
    settings_templates = [
        [f"`{t.name}`", t.description] for t in primitives.settings_templates(root)
    ]
    mcp_templates = [
        [f"`{name}`", ", ".join(f"`{s}`" for s in servers) or "None (opt-in)"]
        for name, servers in primitives.mcp_templates(root)
    ]
    cli = [[f"`{c.name}`", f"`{c.usage}`", c.summary] for c in primitives.cli_scripts(root)]
    return {
        "agents": Catalog("specialist agents", ["Agent", "Description", "Model"], agents),
        "workflow-skills": Catalog(
            "workflow skills",
            ["Skill", "Description", "Who Can Invoke"],
            workflow,
        ),
        "domain-skills": Catalog("domain skills", ["Skill", "Description"], domain),
        "rules": Catalog("style rules", ["Rule", "Applies To", "Covers"], rules),
        "settings-templates": Catalog(
            "permission templates",
            ["Template", "What It Allows"],
            settings_templates,
        ),
        "mcp-templates": Catalog("MCP templates", ["Template", "MCP Servers"], mcp_templates),
        "cli-scripts": Catalog("CLI scripts", ["Script", "Usage", "What It Does"], cli),
    }


def _counts_line(tables: dict[str, Catalog], hook_count: int) -> str:
    n = {name: len(catalog.rows) for name, catalog in tables.items()}
    parts = [
        f"{n['agents']} specialist agents",
        f"{n['workflow-skills'] + n['domain-skills']} skills",
        f"{n['settings-templates']} permission templates",
        f"{n['mcp-templates']} MCP templates",
        f"{hook_count} lifecycle hooks",
        f"{n['rules']} style rules",
        f"{n['cli-scripts']} CLI scripts",
    ]
    return " · ".join(f"`{part}`" for part in parts)


def build_regions(root: Path) -> tuple[dict[str, str], list[str]]:
    """Render every README region; returns ({region name: content}, skill names)."""
    skills = primitives.skills(root)
    bindings = primitives.hook_bindings(root)
    hook_rows = [[f"`{b.label}`", f"`{b.script}`", b.summary] for b in bindings]
    tables = _catalog_tables(root, skills)
    regions = {
        name: details_body(
            f"<strong>{len(catalog.rows)} {catalog.label}</strong>",
            table(catalog.headers, catalog.rows),
        )
        for name, catalog in tables.items()
    }
    regions["hooks"] = details_body(
        f"<strong>{len(hook_rows)} configured hooks</strong> + opt-in",
        "**Configured:**\n\n" + table(["Hook", "Script", "What It Does"], hook_rows),
    )
    regions["counts"] = _counts_line(tables, len(hook_rows))
    regions["repo-tree"] = "```\n" + _tree(root, primitives.hook_triggers(bindings)) + "\n```"
    regions = {name: fence(content) for name, content in regions.items()}
    return regions, [s.name for s in skills]


def uncurated_skills(readme_text: str, skill_names: list[str]) -> list[str]:
    """Soft-warning list: skills the hand-written cheat-sheet never mentions."""
    start = readme_text.find(CHEATSHEET_HEADING)
    if start == -1:
        return [f"README has no {CHEATSHEET_HEADING!r} section to check skill curation against"]
    end = readme_text.find("\n### ", start + len(CHEATSHEET_HEADING))
    section = readme_text[start : end if end != -1 else len(readme_text)]
    return [
        f"skill '{name}' appears in no \"I want to…\" cheat-sheet row"
        for name in skill_names
        if not re.search(rf"(^|[^A-Za-z0-9_-]){re.escape(name)}([^A-Za-z0-9_-]|$)", section)
    ]
