"""Region content builders for generate.py's 'readme' target (issue #112).

Each builder renders one README generated region from the primitives on
disk, so the catalogs cannot disagree with what ships: descriptions render
verbatim from their canonical source (skill/agent frontmatter, hook and CLI
script header comments, template `_description` keys — byte-for-byte except
for the markdown escaping _escape documents), and derived columns
(who-can-invoke, the workflow/domain split, MCP server lists, counts) are
computed, never hand-written. The repository tree's hook and CLI branches
are enumerated from disk; its fixed skeleton is curated in _TREE below —
this module is that region's source, so skeleton edits belong here.

Every region is wrapped in prettier-ignore fences: prettier re-pads
markdown tables, and the generator — not prettier — owns region formatting
(the same reasoning that put settings.json in .prettierignore).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import NamedTuple

from lib.config_common import GenerationError, load_json, parse_frontmatter


class Catalog(NamedTuple):
    """One plain table region: its badge-count label, headers, and rows."""

    label: str
    headers: list[str]
    rows: list[list[str]]


class Skill(NamedTuple):
    name: str
    description: str
    workflow: bool
    invoke: str


# Skills fired by the scheduled cloud routines — daily standup (issue #51)
# and end-of-week review (issue #52). No frontmatter key records scheduling,
# so the routine->skill mapping is declared here. It feeds the
# who-can-invoke column, and _skills enforces the scheduling invariant
# (CONTEXT.md): a scheduled skill must stay model-invocable.
SCHEDULED_SKILLS = frozenset({"standup", "eow-review"})

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
    ├── check-docs-drift.sh  # CI: every primitive documented
    ├── check-context-budget.py  # CI: always-loaded context ≤ byte budget
    ├── check-agent-frontmatter.py  # CI: agent frontmatter contract holds
    ├── lib/                 # Shared Python helpers (config_common, readme_catalogs)
    ├── hooks/               # Hook scripts (annotated with their trigger)
{hook_lines}
    └── cli/                 # Headless CLI automation scripts
{cli_lines}"""


def _escape(cell: str) -> str:
    """Escape table/emphasis metacharacters so verbatim text renders verbatim.

    `_` and `*` are escaped only outside code spans (backslashes would be
    literal inside backticks); escaping keeps glob-like prose such as
    `test_*` from being parsed — and reformatted — as emphasis.
    """
    parts = cell.replace("|", "\\|").split("`")
    for i in range(0, len(parts), 2):
        parts[i] = parts[i].replace("_", "\\_").replace("*", "\\*")
    return "`".join(parts)


def _table(headers: list[str], rows: list[list[str]]) -> str:
    grid = [headers] + [[_escape(cell) for cell in row] for row in rows]
    widths = [max(len(row[i]) for row in grid) for i in range(len(headers))]

    def render(row: list[str]) -> str:
        return "| " + " | ".join(c.ljust(w) for c, w in zip(row, widths)) + " |"

    separator = "| " + " | ".join("-" * w for w in widths) + " |"
    return "\n".join([render(grid[0]), separator] + [render(row) for row in grid[1:]])


def _details_body(summary: str, body: str) -> str:
    """Inner content of a <details> element; the tag itself is hand-written."""
    return f"<summary>{summary} — click to expand</summary>\n\n{body}"


def _fence(content: str) -> str:
    # The blank line before ignore-start is load-bearing: without it the
    # comment merges into the preceding HTML block (e.g. `<details>` + the
    # BEGIN marker) and prettier never sees the directive.
    return f"\n<!-- prettier-ignore-start -->\n{content}\n<!-- prettier-ignore-end -->"


def _read_meta(path: Path) -> dict:
    meta = parse_frontmatter(path)
    description = meta.get("description")
    if not description or not isinstance(description, str):
        raise GenerationError(f"no description: frontmatter in {path}")
    return meta


def _script_header(path: Path) -> list[str]:
    if not path.is_file():
        raise GenerationError(f"script not found: {path}")
    header = []
    for line in path.read_text().splitlines()[1:]:
        if not line.startswith("#"):
            break
        header.append(line.lstrip("#").strip())
    return header


def _script_summary(path: Path) -> str:
    for line in _script_header(path):
        if line:
            return line
    raise GenerationError(f"no header comment to describe {path}")


def _agents(root: Path) -> list[list[str]]:
    rows = []
    for path in sorted((root / "agents").glob("*.md")):
        meta = _read_meta(path)
        rows.append([f"`@{path.stem}`", meta["description"], f"`{meta.get('model', 'inherit')}`"])
    return rows


def _invoke_column(name: str, user_only: bool) -> str:
    if user_only:
        return "you only"
    if name in SCHEDULED_SKILLS:
        return "you, Claude, or a schedule"
    return "you or Claude"


def _skills(root: Path) -> list[Skill]:
    skills = []
    for path in sorted((root / "skills").glob("*/SKILL.md")):
        meta = _read_meta(path)
        name = path.parent.name
        flag = meta.get("disable-model-invocation")
        if flag not in (None, "true", "false"):
            raise GenerationError(f"unrecognised disable-model-invocation value {flag!r} in {path}")
        user_only = flag == "true"
        if user_only and name in SCHEDULED_SKILLS:
            raise GenerationError(
                f"scheduling invariant: skill '{name}' is fired by a scheduled cloud "
                f"routine (see SCHEDULED_SKILLS) but sets disable-model-invocation: true"
            )
        # Workflow skills are the explicitly-invoked ones; on disk that is
        # exactly the set carrying an argument-hint or a
        # disable-model-invocation key. Domain skills carry neither.
        workflow = user_only or "argument-hint" in meta
        skills.append(Skill(name, meta["description"], workflow, _invoke_column(name, user_only)))
    return skills


def _rules(root: Path) -> list[list[str]]:
    rows = []
    for path in sorted((root / "rules").glob("*.md")):
        paths = parse_frontmatter(path).get("paths") or []
        if isinstance(paths, str):
            paths = [paths]
        headings = [ln[3:].strip() for ln in path.read_text().splitlines() if ln.startswith("## ")]
        rows.append([f"`{path.stem}`", ", ".join(f"`{p}`" for p in paths), ", ".join(headings)])
    return rows


def _hooks(root: Path) -> tuple[list[list[str]], dict[str, str]]:
    """Rows for the hooks table, plus {script name: trigger(s)} for the tree."""
    source = root / "hooks" / "hooks.json"
    hooks = load_json(source).get("hooks")
    if not hooks:
        raise GenerationError(f"no 'hooks' key in {source}")
    flat = [(event, entry) for event, entries in hooks.items() for entry in entries]
    rows: list[list[str]] = []
    triggers: dict[str, list[str]] = {}
    for event, entry in flat:
        matcher = entry.get("matcher")
        label = f"{event} ({matcher})" if matcher else event
        for hook in entry.get("hooks", []):
            script = hook.get("command", "").rsplit("/", 1)[-1]
            triggers.setdefault(script, []).append(label)
            summary = _script_summary(root / "scripts" / "hooks" / script)
            rows.append([f"`{label}`", f"`{script}`", summary])
    # A script wired to several events lists every trigger in its tree note.
    return rows, {script: ", ".join(dict.fromkeys(labels)) for script, labels in triggers.items()}


def _settings_templates(root: Path) -> list[list[str]]:
    rows = []
    for path in sorted((root / "settings-templates").glob("*.json")):
        description = load_json(path).get("_description")
        if not description:
            raise GenerationError(f"no _description key in {path} (feeds the README table)")
        rows.append([f"`{path.stem}`", description])
    return rows


def _mcp_templates(root: Path) -> list[list[str]]:
    rows = []
    for path in sorted((root / "mcp-templates").glob("*.json")):
        servers = sorted(load_json(path).get("mcpServers") or {})
        cell = ", ".join(f"`{name}`" for name in servers) or "None (opt-in)"
        rows.append([f"`{path.stem}`", cell])
    return rows


def _cli_scripts(root: Path) -> list[list[str]]:
    rows = []
    for path in sorted((root / "scripts" / "cli").glob("*.sh")):
        header = _script_header(path)
        usage = next(
            (ln.split("Usage:", 1)[1].strip() for ln in header if "Usage:" in ln), path.name
        )
        rows.append([f"`{path.name}`", f"`{usage}`", _script_summary(path)])
    return rows


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
    workflow = [[f"`/{s.name}`", s.description, s.invoke] for s in skills if s.workflow]
    domain = [[f"`{s.name}`", s.description] for s in skills if not s.workflow]
    return {
        "agents": Catalog("specialist agents", ["Agent", "Description", "Model"], _agents(root)),
        "workflow-skills": Catalog(
            "workflow skills",
            ["Skill", "Description", "Who Can Invoke"],
            workflow,
        ),
        "domain-skills": Catalog("domain skills", ["Skill", "Description"], domain),
        "rules": Catalog("style rules", ["Rule", "Applies To", "Covers"], _rules(root)),
        "settings-templates": Catalog(
            "permission templates",
            ["Template", "What It Allows"],
            _settings_templates(root),
        ),
        "mcp-templates": Catalog(
            "MCP templates", ["Template", "MCP Servers"], _mcp_templates(root)
        ),
        "cli-scripts": Catalog(
            "CLI scripts", ["Script", "Usage", "What It Does"], _cli_scripts(root)
        ),
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
    skills = _skills(root)
    hook_rows, hook_notes = _hooks(root)
    tables = _catalog_tables(root, skills)
    regions = {
        name: _details_body(
            f"<strong>{len(catalog.rows)} {catalog.label}</strong>",
            _table(catalog.headers, catalog.rows),
        )
        for name, catalog in tables.items()
    }
    regions["hooks"] = _details_body(
        f"<strong>{len(hook_rows)} configured hooks</strong> + opt-in",
        "**Configured:**\n\n" + _table(["Hook", "Script", "What It Does"], hook_rows),
    )
    regions["counts"] = _counts_line(tables, len(hook_rows))
    regions["repo-tree"] = "```\n" + _tree(root, hook_notes) + "\n```"
    regions = {name: _fence(content) for name, content in regions.items()}
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
