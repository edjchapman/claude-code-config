"""Read this repo's primitives off disk, once, for every catalog target.

A *primitive* is an agent, skill, rule, hook binding, template, or CLI
script (CONTEXT.md). Both catalog renderers — README tables
(readme_catalogs.py) and the docs/architecture.md reference lists
(architecture_catalogs.py) — describe the same primitives, so they read
them through this module rather than each walking the tree. Descriptions
come back verbatim from their canonical source; anything derived (who can
invoke a skill, which trigger fires a hook) is computed here so the two
docs cannot disagree about it.
"""

from __future__ import annotations

from pathlib import Path
from typing import NamedTuple

from lib.config_common import GenerationError, load_json, parse_frontmatter

# Skills fired by the scheduled cloud routines — daily standup (issue #51)
# and end-of-week review (issue #52). No frontmatter key records scheduling,
# so the routine->skill mapping is declared here. It feeds the
# who-can-invoke column, and `skills()` enforces the scheduling invariant
# (CONTEXT.md): a scheduled skill must stay model-invocable.
SCHEDULED_SKILLS = {
    "standup": "the daily standup routine (issue #51)",
    "eow-review": "the end-of-week review routine (issue #52)",
}

# The other half of the same invariant: skills that must stay user-only.
# `disable-model-invocation: true` is what keeps them out of every session's
# always-loaded context and stops Claude firing them unbidden — these three
# write to a personal log or backlog, so an auto-fire is a side effect the
# user never asked for. Losing the flag would not make any catalog wrong
# (the column is derived), which is exactly why it needs asserting: the
# regression would be invisible in the docs.
USER_ONLY_SKILLS = frozenset({"status", "refinement", "later"})


class Agent(NamedTuple):
    name: str
    description: str
    model: str


class Skill(NamedTuple):
    name: str
    description: str
    workflow: bool
    user_only: bool

    @property
    def scheduled(self) -> bool:
        return self.name in SCHEDULED_SKILLS


class Rule(NamedTuple):
    name: str
    paths: list[str]
    headings: list[str]


class HookBinding(NamedTuple):
    """One event->script wiring from hooks/hooks.json (ADR-0001)."""

    event: str
    label: str  # event, plus its matcher when it has one
    script: str
    summary: str
    why: str


class Template(NamedTuple):
    name: str
    description: str


class CliScript(NamedTuple):
    name: str
    usage: str
    summary: str


def _read_meta(path: Path) -> dict:
    meta = parse_frontmatter(path)
    description = meta.get("description")
    if not description or not isinstance(description, str):
        raise GenerationError(f"no description: frontmatter in {path}")
    return meta


def script_doc(path: Path) -> tuple[str, str]:
    """A script's (summary, why) from its header comment block.

    The header is the block of `#` lines under the shebang. Its first
    non-empty line is the summary the catalogs render. A paragraph opening
    `Why:` is the item's rationale — it lives here, next to the thing it
    explains, and is projected into docs/architecture.md rather than being
    restated there. Everything else in the header is implementation notes
    for whoever edits the script, and is not projected anywhere.
    """
    if not path.is_file():
        raise GenerationError(f"script not found: {path}")
    header = []
    for line in path.read_text().splitlines()[1:]:
        if not line.startswith("#"):
            break
        header.append(line.lstrip("#").strip())

    summary = next((line for line in header if line), "")
    if not summary:
        raise GenerationError(f"no header comment to describe {path}")

    why: list[str] = []
    for line in header:
        if why:
            if not line:
                break
            why.append(line)
        elif line.startswith("Why:"):
            why.append(line[len("Why:") :].strip())
    return summary, " ".join(why).strip()


def agents(root: Path) -> list[Agent]:
    result = []
    for path in sorted((root / "agents").glob("*.md")):
        meta = _read_meta(path)
        result.append(Agent(path.stem, meta["description"], meta.get("model", "inherit")))
    return result


def skills(root: Path) -> list[Skill]:
    result = []
    for path in sorted((root / "skills").glob("*/SKILL.md")):
        meta = _read_meta(path)
        name = path.parent.name
        flag = meta.get("disable-model-invocation")
        if flag not in (None, "true", "false"):
            raise GenerationError(f"unrecognised disable-model-invocation value {flag!r} in {path}")
        user_only = flag == "true"
        if user_only and name in SCHEDULED_SKILLS:
            raise GenerationError(
                f"scheduling invariant: skill '{name}' is fired by {SCHEDULED_SKILLS[name]} "
                f"but sets disable-model-invocation: true, which blocks scheduled tasks "
                f"from running it (v2.1.196+) and orphans the routine"
            )
        if not user_only and name in USER_ONLY_SKILLS:
            raise GenerationError(
                f"scheduling invariant: skill '{name}' is declared user-only "
                f"(USER_ONLY_SKILLS) but does not set disable-model-invocation: true, "
                f"so Claude can now auto-fire it and it costs always-loaded context"
            )
        # Workflow skills are the explicitly-invoked ones; on disk that is
        # exactly the set carrying an argument-hint or a
        # disable-model-invocation key. Domain skills carry neither.
        workflow = user_only or "argument-hint" in meta
        result.append(Skill(name, meta["description"], workflow, user_only))
    return result


def rules(root: Path) -> list[Rule]:
    result = []
    for path in sorted((root / "rules").glob("*.md")):
        paths = parse_frontmatter(path).get("paths") or []
        if isinstance(paths, str):
            paths = [paths]
        headings = [ln[3:].strip() for ln in path.read_text().splitlines() if ln.startswith("## ")]
        result.append(Rule(path.stem, paths, headings))
    return result


def hook_bindings(root: Path) -> list[HookBinding]:
    """Every event->script wiring in hooks/hooks.json, in file order."""
    source = root / "hooks" / "hooks.json"
    hooks = load_json(source).get("hooks")
    if not hooks:
        raise GenerationError(f"no 'hooks' key in {source}")
    result = []
    for event, entries in hooks.items():
        for entry in entries:
            matcher = entry.get("matcher")
            label = f"{event} ({matcher})" if matcher else event
            for hook in entry.get("hooks", []):
                script = hook.get("command", "").rsplit("/", 1)[-1]
                summary, why = script_doc(root / "scripts" / "hooks" / script)
                result.append(HookBinding(event, label, script, summary, why))
    return result


def hook_triggers(bindings: list[HookBinding]) -> dict[str, str]:
    """{script name: every trigger that fires it}, for the repo-tree notes."""
    triggers: dict[str, list[str]] = {}
    for binding in bindings:
        triggers.setdefault(binding.script, []).append(binding.label)
    return {script: ", ".join(dict.fromkeys(labels)) for script, labels in triggers.items()}


def settings_templates(root: Path) -> list[Template]:
    result = []
    for path in sorted((root / "settings-templates").glob("*.json")):
        description = load_json(path).get("_description")
        if not description:
            raise GenerationError(f"no _description key in {path} (feeds the generated catalogs)")
        result.append(Template(path.stem, description))
    return result


def mcp_templates(root: Path) -> list[tuple[str, list[str]]]:
    """[(template name, sorted MCP server names)] — the servers it wires."""
    return [
        (path.stem, sorted(load_json(path).get("mcpServers") or {}))
        for path in sorted((root / "mcp-templates").glob("*.json"))
    ]


def cli_scripts(root: Path) -> list[CliScript]:
    result = []
    for path in sorted((root / "scripts" / "cli").glob("*.sh")):
        summary, _ = script_doc(path)
        usage = path.name
        for line in path.read_text().splitlines()[1:]:
            if not line.startswith("#"):
                break
            if "Usage:" in line:
                usage = line.split("Usage:", 1)[1].strip()
                break
        result.append(CliScript(path.name, usage, summary))
    return result
