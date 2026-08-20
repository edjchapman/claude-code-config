# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Purpose

This is a configuration repository for Claude Code. It can be consumed two ways:

1. **As a plugin** (recommended): `/plugin marketplace add edjchapman/claude-code-config`, then `/plugin install claude-code-config`. The plugin name resolves only against marketplaces you have added — there is no global registry — so this can only install from this repo. If another added marketplace also defines a `claude-code-config` plugin, disambiguate with `/plugin install claude-code-config@claude-code-config` (`plugin@marketplace`). The plugin loader sets `CLAUDE_PLUGIN_ROOT` and the hook commands resolve relative to that.
2. **As a symlinked global config** (legacy path, still supported): `scripts/setup-global.sh` symlinks `agents/`, `skills/`, `rules/`, and `settings.json` into `~/.claude/`. Per-project use is via `scripts/setup-project.sh`.

The two modes coexist — hook command paths use `${CLAUDE_PLUGIN_ROOT:-<readlink fallback>}`, so they resolve in both modes without modification.

## Where the reference lives

This file is loaded into **every session**, so it carries only the behavioural rules and easy-to-get-wrong gotchas below. The full reference is split out (and is not auto-loaded — read it when the task calls for it):

- **[`docs/architecture.md`](docs/architecture.md)** — Key Scripts, Hooks (formats, handler types, the full hook catalog + opt-in snippets), Settings Keys, Skills/Rules listings, Settings Files, Settings + MCP template systems, CLI Scripts, Automation & live cloud routines, Agent & Skill Definitions.
- **[`docs/extending.md`](docs/extending.md)** — when to use a skill vs an agent, the plugin-vs-custom retirement policy, the copy-an-exemplar Self-Extension Guide, and prompting techniques.
- **[`README.md`](README.md)** — user-facing catalogs of every agent, skill, hook, and template.

## Working in this repo

These are the rules that are easy to get wrong — keep them in mind whenever you touch this config:

- **Hooks are edited in one place.** `hooks/hooks.json` is the source of truth for hook definitions (ADR-0001); `settings.json`'s `hooks` key is a **generated region** produced by `scripts/generate.py`. Never hand-edit the generated block — edit `hooks/hooks.json` and let pre-commit regenerate (or run `python3 scripts/generate.py`). CI enforces freshness via `generate.py --check`. Both files stay committed: each install mode reads its file directly. See [`docs/architecture.md`](docs/architecture.md) for the hook formats and the current catalog.
- **No-matcher events.** These events must omit the `matcher` field (adding one is silently ignored per the docs): `UserPromptSubmit`, `Stop`, `TaskCompleted`, `PostToolBatch`, `TeammateIdle`, `TaskCreated`, `WorktreeCreate`, `WorktreeRemove`, `MessageDisplay`, `CwdChanged`.
- **Every primitive must be named in `CLAUDE.md` or `README.md`.** `scripts/check-docs-drift.sh` fails CI if an agent / skill / hook / template on disk is documented in neither. README's catalogs are **generated regions** (issue #112), so a new primitive appears there by regeneration — provided it carries the description its catalog renders (frontmatter `description:`, a hook/CLI script header comment, or a settings-template `_description` key).
- **Keep issues [#51](https://github.com/edjchapman/claude-code-config/issues/51) and [#52](https://github.com/edjchapman/claude-code-config/issues/52) open** — they are the delivery targets for the daily-standup and end-of-week cloud routines; closing one orphans its routine.
- **Run the validation suite before pushing** (CI runs the same checks):

```bash
python3 -m json.tool settings.json > /dev/null   # JSON sanity
scripts/hooks/check-duplicates.sh                # No agent/skill/command name collisions
python3 scripts/generate.py --check              # Generated regions fresh (settings.json hooks key, README catalogs)
scripts/check-docs-drift.sh                      # Every primitive is documented
python3 scripts/check-context-budget.py          # Always-loaded context within byte budget
python3 scripts/check-agent-frontmatter.py       # Agent frontmatter contract (keys, name==filename)
python3 scripts/check-settings-keys.py           # settings.json top-level keys allowlisted
```

## Scope and Implementation Philosophy

### Strict Scope Adherence

When the user specifies a task, treat the scope as a contract:

- Focus strictly on the scope specified. Do not touch files or add changes beyond what was requested without explicit approval.
- If you discover the task requires changes beyond the stated scope, **pause and describe** what you've found. Get explicit user approval before expanding scope.
- Never assume scope expansion is welcome, even if architecturally cleaner.

### Root Cause Over Symptom Fixes

When fixing bugs, always address the root cause rather than applying symptom-level bandaids:

- Trace errors to their earliest origin point — fix division-by-zero at the calculation layer, not with `fillna` in serialization.
- If you still need a secondary bandaid after fixing the root cause, the root cause fix was incomplete.

### Test Safety Net Before Refactoring

Never refactor without a safety net. Before restructuring code, verify that tests exist for the behavior being changed. If they don't, write them first. Tests must pass before, during, and after every refactoring step.

### Derivation Over Duplication

When refactoring or adding new config/constants, always derive from existing sources of truth rather than duplicating logic. Check for existing constants, registries, or config objects before creating new ones.

### Adopt User Corrections Immediately

When the user asks to narrow scope or correct an approach, immediately adopt their direction without further deliberation or alternative proposals. The user knows the codebase constraints.

## Code Style

- Shell scripts: Linted with `shellcheck` (CI validates on every push)
- Python: Linted with `ruff` (auto-formatted by `format-on-edit` hook)
- JSON: Validated with `python -m json.tool` (CI validates templates and merge outputs)

## Tooling Troubleshooting

If a tool or integration isn't working (e.g., MCP server, browser extension, external API), pivot after 2 failed attempts rather than retrying across the entire session. Suggest an alternative approach or escalate to the user. The cost of continued retrying far exceeds the cost of asking for help.

## Commit Messages

Follow conventional commits:

```
feat(agents): add kubernetes-helper agent
fix(scripts): handle spaces in paths
docs: update template documentation
```

## Agent skills

### Issue tracker

Issues live in this repo's GitHub Issues, operated via the `gh` CLI. See `docs/agents/issue-tracker.md`.

### Triage labels

Default canonical labels: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context layout — root `CONTEXT.md` + `docs/adr/` (created lazily). See `docs/agents/domain.md`.
