"""Region content builders for generate.py's 'architecture' target (issue #114).

docs/architecture.md is the Claude-facing reference: every catalog in it
mirrors primitives that already exist on disk, so those mirrors are
generated (from primitives.py) and only rationale prose is hand-written.
That kills a whole class of stale claim by construction — a hook the repo
wires cannot still be listed as "not yet used", and a settings key the repo
sets cannot still be listed as unset, because both lists are the *difference*
between a declared platform catalog and what is actually on disk.

Two kinds of data live here, and they are different in kind from the
primitives:

  * Facts about the Claude Code platform (its documented hook events, its
    documented settings keys). These describe the harness, not this repo,
    so nothing on disk can supply them — they are declared below with the
    date they were verified against the docs.
  * One-line glosses for the settings keys this repo sets. settings.json
    has nowhere to carry a description, so the gloss is declared beside the
    key. A key with no gloss is an error — the catalog would silently omit
    a key the repo actually sets. A gloss for a key no longer set is only a
    warning: it renders nothing, so it is untidiness rather than a wrong
    document, and failing on it would make the target unrunnable against
    any root but this one.

Per-item rationale that *does* have a source-file home does not live here:
a hook's why-note lives in its script header and is projected
(primitives.script_doc), so the "why" travels with the thing it explains.
"""

from __future__ import annotations

from pathlib import Path
from typing import NamedTuple

from lib import primitives
from lib.catalog_render import bullets, escape_inline, fence, table
from lib.config_common import GenerationError, load_json

# Hook events Claude Code documents, verified against the hooks reference
# (https://code.claude.com/docs/en/hooks.md) on 2026-07-29. The catalog is
# declared rather than derived because it describes the harness, not this
# repo. Only the count is used from here directly; the *table* is this list
# minus whatever hooks/hooks.json wires today, so an event this repo adopts
# leaves the "not wired" list — and takes its `adopt` note with it —
# without anyone remembering to delete a paragraph.
DOCUMENTED_EVENT_COUNT = 30


class PlatformEvent(NamedTuple):
    name: str
    fires_when: str
    matcher: str
    adopt: str = ""  # why it would be worth wiring here, if it would


UNWIRED_EVENTS = [
    PlatformEvent("Setup", "started with `--init` / `--init-only` / `--maintenance`", "CLI flag"),
    PlatformEvent(
        "PermissionRequest",
        "a tool call needs a permission decision",
        "tool name",
        "could feed a permission-tuning workflow",
    ),
    PlatformEvent(
        "PermissionDenied",
        "a tool call is denied by the auto-mode classifier",
        "tool name",
        "could feed a permission-tuning workflow",
    ),
    PlatformEvent("SubagentStart", "a subagent is spawned", "agent type"),
    PlatformEvent(
        "StopFailure",
        "the turn ends due to an API error",
        "error type (`rate_limit`, `overloaded`, …)",
        "matched on `rate_limit` / `overloaded`, complements the `fallbackModel` chain",
    ),
    PlatformEvent(
        "InstructionsLoaded",
        "a `CLAUDE.md` / `.claude/rules/*.md` loads into context",
        "load reason (`session_start`, `path_glob_match`, …)",
    ),
    PlatformEvent("FileChanged", "a watched file changes on disk", "filename(s) to watch"),
    PlatformEvent("PostCompact", "after context compaction completes", "none (no-matcher)"),
]

# Documented events whose matcher field was not re-verified on that date.
UNVERIFIED_EVENTS = ["UserPromptExpansion", "ConfigChange", "Elicitation", "ElicitationResult"]

# One-line gloss per top-level key settings.json sets. Rationale longer than
# a line stays as prose next to the generated block — this is a catalog, not
# an explanation.
SETTINGS_KEY_GLOSSES = {
    "$schema": "Settings schema URL, for editor completion and validation",
    "attribution": (
        "Git commit/PR attribution text — empty `commit`/`pr` strings and "
        "`sessionUrl: false` suppress the Claude trailers"
    ),
    "fallbackModel": "Ordered fallback chain tried when the primary model is unavailable",
    "hooks": "Per-event hook configuration — generated from `hooks/hooks.json` (ADR-0001)",
    "worktree": (
        "Worktree-session config: `baseRef: head` branches from local HEAD "
        "(preserving unpushed commits); `bgIsolation: worktree` blocks Edit/Write "
        "in the main checkout until `EnterWorktree` is called"
    ),
    "statusLine": "Command-based status line showing git branch, dirty count, and PR status",
    "enabledPlugins": "Plugin enablement map — universal plugins only, some deliberately `false`",
    "extraKnownMarketplaces": "Extra plugin marketplaces this config expects to be available",
    "outputStyle": (
        "Output style for assistant responses (built-ins: `default`, `Explanatory`, `Learning`)"
    ),
    "sandbox": "Sandbox configuration (`enabled`, `autoAllowBashIfSandboxed`)",
    "tui": (
        "TUI rendering mode — `fullscreen` is the flicker-free alt-screen renderer "
        "with virtualized scrollback; `default` is the classic one. Matches `/tui`"
    ),
    "autoMemoryEnabled": "Auto-memory on/off (platform default `true`)",
    "inputNeededNotifEnabled": "Desktop notification when Claude is blocked waiting for you",
    "agentPushNotifEnabled": "Push notifications for background agent activity",
}

# Documented top-level settings keys, with a gloss where the name alone is
# not self-explanatory (verified against the settings docs, 2026-07-29). The
# rendered list is this catalog minus whatever settings.json actually sets.
DOCUMENTED_SETTINGS_KEYS = {
    "env": "",
    "model": "",
    "fileSuggestion": "",
    "spinnerVerbs": "",
    "skillOverrides": "",
    "autoMode": "",
    "alwaysThinkingEnabled": "",
    "parentSettingsBehavior": "",
    "autoMemoryDirectory": "custom auto-memory storage dir",
    "autoMemoryEnabled": "auto-memory on/off, default `true`",
    "availableModels": "restrict selectable models",
    "enforceAvailableModels": "restrict selectable models",
    "axScreenReader": "screen-reader-friendly output",
    "fastMode": "faster Opus output, default `false`",
    "language": "response language preference",
    "cleanupPeriodDays": "session file retention, default 30",
    "disableBundledSkills": "hide bundled skills like `/code-review`, `/loop`",
    "effortLevel": "default reasoning effort",
    "statusLine": "",
    "attribution": "",
    "fallbackModel": "",
    "hooks": "",
    "worktree": "",
    "enabledPlugins": "",
    "outputStyle": "",
    "sandbox": "",
    "tui": "",
    "inputNeededNotifEnabled": "",
    "agentPushNotifEnabled": "",
    "extraKnownMarketplaces": "",
}


def _hooks(root: Path) -> str:
    bindings = primitives.hook_bindings(root)
    items = []
    for binding in bindings:
        # Script summaries are written as headline comments; some end in a
        # full stop and some don't, and the bullet needs exactly one.
        summary = escape_inline(binding.summary.rstrip("."))
        note = f" _Why:_ {escape_inline(binding.why)}" if binding.why else ""
        items.append(f"**{binding.label}** → `scripts/hooks/{binding.script}`: {summary}.{note}")
    lead = (
        f"Wired in [`hooks/hooks.json`](../hooks/hooks.json) — "
        f"{len(bindings)} bindings across {len({b.event for b in bindings})} events:"
    )
    return f"{lead}\n\n{bullets(items)}"


def _unwired_events(root: Path) -> str:
    wired = {binding.event for binding in primitives.hook_bindings(root)}
    unwired = [event for event in UNWIRED_EVENTS if event.name not in wired]
    lead = (
        f"Claude Code documents **{DOCUMENTED_EVENT_COUNT}** hook events; this repo wires "
        f"{len(wired)} of them above. Documented events it does not wire, with their matcher "
        f"field where confirmed against the docs on 2026-07-29:"
    )
    grid = table(
        ["Event", "Fires when", "Matcher field"],
        [[f"`{e.name}`", e.fires_when, e.matcher] for e in unwired],
    )
    also = (
        "Also available (matcher fields not re-verified here — consult the hooks reference "
        "before wiring): " + ", ".join(f"`{name}`" for name in UNVERIFIED_EVENTS) + "."
    )
    parts = [lead, grid, also]
    # Events sharing a rationale are named together rather than repeating it.
    grouped: dict[str, list[str]] = {}
    for event in unwired:
        if event.adopt:
            grouped.setdefault(event.adopt, []).append(event.name)
    if grouped:
        notes = [
            " / ".join(f"**`{name}`**" for name in names) + f" {adopt}"
            for adopt, names in grouped.items()
        ]
        parts.append("Most useful to adopt here: " + "; ".join(notes) + ".")
    return "\n\n".join(parts)


def _settings_keys(root: Path) -> tuple[str, list[str]]:
    keys = list(load_json(root / "settings.json"))
    missing = [key for key in keys if key not in SETTINGS_KEY_GLOSSES]
    if missing:
        raise GenerationError(
            f"settings.json key(s) {missing} have no gloss — add one to "
            f"SETTINGS_KEY_GLOSSES in lib/architecture_catalogs.py"
        )
    warnings = [
        f"SETTINGS_KEY_GLOSSES describes `{key}`, which settings.json no longer sets"
        for key in SETTINGS_KEY_GLOSSES
        if key not in keys
    ]
    return bullets([f"**`{key}`**: {SETTINGS_KEY_GLOSSES[key]}" for key in keys]), warnings


def _unset_settings_keys(root: Path) -> str:
    set_keys = set(load_json(root / "settings.json"))
    unset = [key for key in sorted(DOCUMENTED_SETTINGS_KEYS) if key not in set_keys]
    rendered = ", ".join(
        f"`{key}`"
        + (f" ({DOCUMENTED_SETTINGS_KEYS[key]})" if DOCUMENTED_SETTINGS_KEYS[key] else "")
        for key in unset
    )
    return f"Other documented keys this repo does **not** set (available as opt-ins): {rendered}."


def _skills(root: Path) -> str:
    skills = primitives.skills(root)
    domain = [s for s in skills if not s.workflow]
    workflow = [s for s in skills if s.workflow]

    def workflow_item(skill: primitives.Skill) -> str:
        mark = ""
        if skill.user_only:
            mark = " **User-only.**"
        elif skill.scheduled:
            mark = f" **Schedulable** — fired by {primitives.SCHEDULED_SKILLS[skill.name]}."
        return f"`/{skill.name}`: {escape_inline(skill.description)}{mark}"

    return "\n\n".join(
        [
            "**Domain-knowledge skills** — Claude loads these automatically when the "
            "conversation matches their `description:`:",
            bullets([f"`{s.name}`: {escape_inline(s.description)}" for s in domain]),
            "**Workflow skills** — invoked as `/<name>`; those without "
            "`disable-model-invocation` can also be auto-invoked by Claude:",
            bullets([workflow_item(s) for s in workflow]),
        ]
    )


def _rules(root: Path) -> str:
    return bullets(
        [
            f"`{rule.name}`: {', '.join(rule.headings)} ({', '.join(f'`{p}`' for p in rule.paths)})"
            for rule in primitives.rules(root)
        ]
    )


def _settings_templates(root: Path) -> str:
    templates = primitives.settings_templates(root)
    lead = f"Available templates ({len(templates)}):"
    return (
        lead + "\n\n" + bullets([f"`{t.name}`: {escape_inline(t.description)}" for t in templates])
    )


def _mcp_templates(root: Path) -> str:
    items = []
    for name, servers in primitives.mcp_templates(root):
        wired = ", ".join(f"`{server}`" for server in servers) or "**no MCP server** (opt-in)"
        items.append(f"`{name}`: {wired}")
    return "Available MCP templates:\n\n" + bullets(items)


def _cli_scripts(root: Path) -> str:
    def item(script: primitives.CliScript) -> str:
        # Only worth showing the invocation when it is not just the filename
        # (explain-error.sh is meant to be piped into, and reads oddly bare).
        call = f" — invoke as `{script.usage}`" if script.usage != script.name else ""
        return f"`{script.name}`: {escape_inline(script.summary)}{call}"

    return bullets([item(script) for script in primitives.cli_scripts(root)])


def build_regions(root: Path) -> tuple[dict[str, str], list[str]]:
    """Render every docs/architecture.md region; returns (regions, warnings)."""
    settings_keys, warnings = _settings_keys(root)
    regions = {
        "arch-hooks": _hooks(root),
        "arch-unwired-events": _unwired_events(root),
        "arch-settings-keys": settings_keys,
        "arch-unset-settings-keys": _unset_settings_keys(root),
        "arch-skills": _skills(root),
        "arch-rules": _rules(root),
        "arch-settings-templates": _settings_templates(root),
        "arch-mcp-templates": _mcp_templates(root),
        "arch-cli-scripts": _cli_scripts(root),
    }
    return {name: fence(content) for name, content in regions.items()}, warnings
