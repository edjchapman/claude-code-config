# Extending & customizing this config

How to choose between a skill and an agent, what stays custom vs delegated to a plugin, the copy-an-exemplar recipes for adding new primitives, and prompting tips. See also [`architecture.md`](architecture.md) for the reference catalog and [`CLAUDE.md`](../CLAUDE.md) for behavioural rules.

## Skills and Agents — when to use each

Two primitives, three usage patterns; picking the right one keeps the skill picker uncluttered. (A former third primitive, `commands/`, was merged into skills — a "command" is now just a skill with `disable-model-invocation: true`.)

| Use a...                                         | When                                                                                                                                                                                                                                                                          | Example in this repo                                                                                            |
| ------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| **Domain skill** (`skills/`, default invocation) | Domain knowledge you want Claude to load automatically based on the conversation (matched from the skill's `description:`)                                                                                                                                                    | `django-patterns` (loads when editing Django models/views), `security-patterns` (loads on auth/middleware work) |
| **Workflow skill** (`skills/`)                   | A repeatable workflow invoked as `/<name>`. Leave auto-invocation on when Claude firing it from context is welcome (`/commit`, `/hotfix`); add `disable-model-invocation: true` when only you should trigger it (`/later`, `/status`) or it has side effects you want to time | `/commit`, `/standup`, `/later`                                                                                 |
| **Agent** (`agents/`)                            | Specialist `@agent-name` task with a forked context — deep, single-domain work that shouldn't pollute the main conversation                                                                                                                                                   | `@bug-resolver`, `@database-architect`, `@performance-engineer`                                                 |

Rule of thumb: if the action is **domain knowledge Claude should load automatically**, it wants to be a domain skill. If it's a **repeatable workflow** ("commit my work", "give me a standup summary"), it wants to be a workflow skill — user-only via `disable-model-invocation: true` when timing or side effects matter. If it's **scoped expertise that benefits from isolation** ("audit this for security"), it wants to be an agent.

## Plugin vs custom — what stays in this repo

Several enabled plugins (visible in `settings.json`'s `enabledPlugins`) overlap with what custom agents/commands could provide. The rule applied during the modernization sweep:

> **Retire custom only when the plugin fully subsumes its purpose AND the plugin is already enabled.** Borderline cases stay custom.

Currently retired in favor of plugins:

| Retired                                            | Replaced by                                                                                            |
| -------------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| `agents/code-reviewer.md`                          | `pr-review-toolkit:code-reviewer` (depth) + `feature-dev:code-reviewer` (confidence-filtered)          |
| `agents/spec-writer.md`                            | `feature-dev:code-architect`                                                                           |
| `commands/review.md`                               | bundled `/review`                                                                                      |
| `commands/security-scan.md`                        | bundled `/security-review`                                                                             |
| `commands/deps.md` (delegation wrapper)            | `@dependency-manager` (the agent auto-detects npm/pip/uv/poetry/go/cargo)                              |
| `commands/coverage-report.md` (delegation wrapper) | `@test-engineer` (the agent auto-detects Django/Jest/Vitest and analyzes coverage gaps)                |
| `agents/pr-review-bundler.md`                      | `pr-review-toolkit:review-pr`                                                                          |
| `agents/refactoring-engineer.md`                   | `code-simplifier` plugin + bundled `/simplify`                                                         |
| `agents/security-auditor.md`                       | bundled `/security-review` + `skills/security-patterns` (domain knowledge)                             |
| `agents/e2e-playwright-engineer.md`                | `@test-engineer` (absorbed the E2E/Playwright conventions) + `playwright` plugin (MCP tools)           |
| `agents/git-helper.md`                             | `git-workflow` skill (absorbed the recovery/rebase/bisect content)                                     |
| `agents/migration-engineer.md`                     | `@database-architect` (expand-contract, migration sizing) + `@dependency-manager` (framework upgrades) |
| `skills/tdd/`                                      | `mattpocock-skills:tdd` (same red-green-refactor loop; exact trigger collision while both existed)     |
| `skills/root-cause-analysis/`                      | `mattpocock-skills:diagnosing-bugs` (same trigger domain: bugs, regressions, failures, slowness)       |

Kept custom because no enabled plugin fully covers them:

- `@bug-resolver`, `@ci-debugger`, `@database-architect`, `@dependency-manager`, `@devops-engineer`, `@documentation-writer`, `@performance-engineer`, `@test-engineer`
- `/commit`, `/pr`, `/hotfix`, `/adr`, `/standup`, `/status`, `/refinement`, `/eow-review`, `/later`

If you enable a new plugin and it overlaps with one of the kept-custom items, re-apply the rule.

Rule re-applied for `mattpocock-skills@mattpocock` (enabled 2026-07-31, via the `mattpocock` marketplace in `extraKnownMarketplaces`): its `tdd`, `code-review`, `research`, and `diagnosing-bugs` skills overlap with custom `/tdd`, the bundled `/code-review`, `/deep-research`, and the `root-cause-analysis` skill respectively. Initially all four were judged borderline; the 2026-07-31 token-efficiency review reversed two of those calls — `tdd` and `root-cause-analysis` were retired (see table above) because keeping both made skill invocation ambiguous (an exact trigger collision means which one fires is a coin flip). The `code-review` and `research` overlaps are with _bundled_ commands, not repo customs, so nothing to retire there. The plugin's additive value is the grilling suite (`grilling`, `grill-me`, `grill-with-docs`), the spec→ticket pipeline (`to-spec`, `to-tickets`, `triage`, `wayfinder`, `implement` — run its `setup-matt-pocock-skills` once per repo first), the design-vocabulary skills (`codebase-design`, `domain-modeling`), and productivity extras (`handoff`, `teach`, `writing-great-skills`, `prototype`).

## What earns always-loaded context

Every primitive has a fixed per-session token cost and an on-demand cost. When adding something new, put it at the **cheapest rung that still triggers reliably** (ascending fixed cost):

1. **Path-scoped rule** (`rules/*.md` with `paths:` frontmatter) — **zero** fixed cost; the body loads only when Claude reads a file matching the globs. Best for file-type conventions (style, idioms). Caveat: rules ship only via the symlink install path — plugin-mode consumers of this repo don't receive them.
2. **Skill** — the `description:` (~150 B) loads every session; the body loads on invocation. Best for invocable workflows and conversation-triggered domain knowledge. Keep descriptions tight — they are the per-session cost.
3. **Agent** — the description loads every session, but the agent runs in its **own context window**, so delegating to one _relieves_ main-session context pressure. Best for bulk or specialist work whose intermediate output shouldn't pollute the conversation.
4. **CLAUDE.md line** — full cost, every session, every project (for `home/CLAUDE.md`). Only for cross-cutting behavioural rules that must always apply. Reference material belongs in `docs/` (linked, not loaded).
5. **Plugin** — heaviest and all-or-nothing: an enabled plugin ships _all_ of its skill/agent/command descriptions (and sometimes MCP tools) into every session. Enable by default only when most sessions benefit; otherwise leave it disabled in `settings.json` and enable per-machine or per-project.

Two enforcement mechanisms back this ladder: `scripts/check-context-budget.py` (CI) fails when the always-loaded surface exceeds its budget, and one canonical skill per trigger — when two skills share a trigger (as `/tdd` and `mattpocock-skills:tdd` briefly did), which one fires is nondeterministic, so resolve the collision rather than tolerate it.

## Self-Extension Guide

When extending this repo (adding a new agent / skill / command / hook / template), copy the most-similar exemplar rather than writing frontmatter from scratch. The exemplars below have been verified against the canonical Claude Code docs.

### Add an agent

- **Where**: `agents/<kebab-name>.md`
- **Required frontmatter**: `name`, `description` — a rich `"<what it does>. Use when <trigger>"` phrasing (this repo's convention; no agent uses `<example>` blocks and they trigger fine on the prose)
- **Optional**: `model` (`opus`/`sonnet`/`haiku`), `tools`, `disallowedTools`, `color`, `permissionMode`, `memory` (`user`/`project`/`local` — cross-session learning), `isolation: worktree`
- **Model heuristic**: omit `model` so the agent **inherits** the session model — the right default for deep-reasoning agents (bug-resolver, database-architect). Pin only for deliberate cost routing: `sonnet` for pattern-based work (test-engineer, documentation-writer), `haiku` for highly-structured data-plumbing
- **Exemplar**: [`agents/bug-resolver.md`](../agents/bug-resolver.md) — inherits the session model (no `model:` pin), with a rich `description` + `Use when` trigger

### Add a skill

- **Where**: `skills/<kebab-name>/SKILL.md` (nested layout — one directory per skill; the directory name is the `/name`)
- **Required frontmatter**: `description` — write it as `"<what it does>. Use when <user trigger phrasing>."` so Claude loads it from the conversation
- **Optional**: `argument-hint`, `allowed-tools`, `disallowed-tools`, `disable-model-invocation: true`, `user-invocable: false`, `model`, `effort`, `when_to_use`, `paths`, `context: fork`
- **Domain-knowledge exemplar**: [`skills/django-patterns/SKILL.md`](../skills/django-patterns/SKILL.md)
- **Workflow exemplar (user-only)**: [`skills/later/SKILL.md`](../skills/later/SKILL.md) — for workflows only you should trigger, add `disable-model-invocation: true`; remember that flag also blocks scheduled tasks from running the skill (which is why `standup`/`eow-review` omit it)

### Add a hook

- **Prompt-type hooks need no script**: for LLM-evaluated gates, add a `{ "type": "prompt", "prompt": "..." }` entry directly to both hook files (exemplar: the opt-in `Stop` snippet in the Hooks section). The steps below cover command-type hooks.
- **Script location**: `scripts/hooks/<name>.sh` (set `chmod +x`, include `#!/usr/bin/env bash`)
- **Wire-up — one file**: add the entry to `hooks/hooks.json` (under `hooks.<EventName>` inside the top-level `{"hooks": {...}}` wrapper); pre-commit regenerates `settings.json`'s hooks block from it (ADR-0001), or run `python3 scripts/generate.py`. Use a `command` value of `"${CLAUDE_PLUGIN_ROOT:-$(readlink ~/.claude/settings.json | xargs dirname)}/scripts/hooks/<name>.sh"` so it resolves in both plugin and symlink-global modes.
- **Matcher rules**: most events support a `matcher` field — tool events filter on tool name (e.g. `"Bash"`, `"Edit|Write"`); other events filter on event-specific fields (e.g. `SessionStart` on start reason, `SessionEnd` on exit reason, `SubagentStop` on agent type). Events that **don't** support matchers and must omit the field: `UserPromptSubmit`, `Stop`, `TaskCompleted`, `PostToolBatch`, `TeammateIdle`, `TaskCreated`, `WorktreeCreate`, `WorktreeRemove`, `MessageDisplay`, `CwdChanged`. See [hooks reference](https://code.claude.com/docs/en/hooks.md) for the full per-event schema.
- **Exemplar wire-up**: any current entry in `settings.json` or `hooks/hooks.json` under `hooks.*`

### Add a settings template

- **Where**: `settings-templates/<stack>.json`
- **Schema**: `_source`, `_version`, `permissions.allow`, `permissions.deny`
- **Precedence**: `deny` beats `allow` during merge — use deny lists for stack-specific footguns (e.g. `terraform.json` denying `terraform destroy:*`)
- **Exemplar**: [`settings-templates/django.json`](../settings-templates/django.json)

### After extending

Run the validation suite locally before pushing:

```bash
pre-commit run --all-files                # Formatters, linters, and every standing checker
python3 scripts/generate.py --check       # Generated regions fresh; hook and scheduling invariants
python3 -m unittest discover -s tests     # Generator CLI tests
```

A new primitive needs no docs edit: the README catalogs and
[`architecture.md`](architecture.md)'s reference lists are generated from
what it carries — frontmatter `description:`, a script header comment, or a
template `_description`. Regenerate (or let pre-commit do it) and it is
listed.

CI (`.github/workflows/validate-config.yml`) runs the same checks.

## Code Style

- Shell scripts: Linted with `shellcheck` (CI validates on every push)
- Python: Linted with `ruff` (auto-formatted by `format-on-edit` hook)
- JSON: Validated with `python -m json.tool` (CI validates templates and merge outputs)

## Prompting Techniques

A short reference for getting better results from Claude Code in this repo. These are pointers, not full guides — read the [official best-practices doc](https://code.claude.com/docs/en/best-practices.md) for depth.

- **Explore → Plan → Code → Verify.** For non-trivial changes, start in plan mode (Shift+Tab) so Claude reads the relevant code, surfaces edge cases, and produces a written plan before editing. Especially valuable on large refactors and migrations where rework is expensive.
- **Subagents for fan-out and isolation.** Use the Agent tool when you need to read a lot of files (keeps the main context clean) or want a forked context for one specialist task. The Explore subagent is purpose-built for read-only investigation.
- **`/clear` vs `/compact`.** `/clear` resets entirely — use it between unrelated tasks. `/compact <instructions>` keeps the conversation but summarizes it, optionally biased toward what you care about (e.g. `/compact focus on the API changes`).
- **`/goal` for autonomous runs.** Set a completion condition and let Claude work without per-turn prompting. Useful for long migrations or "fix all the failing tests" type sweeps. Live token/turn overlay shows cost.
- **`/ultrareview` for high-stakes reviews.** Multi-agent cloud review. Billed; use when a serious second opinion is worth the cost (security-sensitive merges, large PRs).
- **`/less-permission-prompts`.** Scans your transcripts and proposes allowlist rules for `.claude/settings.json`. Run periodically when you're tired of the same permission prompts.
- **`/btw` for ephemeral questions.** Dismissible overlay; doesn't enter conversation history. Good for "what does X do?" tangents that shouldn't bloat context.
- **Verify before claiming done.** Run the test suite, type-check, or visually test UI in the browser before saying "done". Self-verification is the single biggest leverage point for output quality.
- **CLAUDE.md hygiene.** This file is loaded into every session — keep it under 1,000 lines and prune ruthlessly when something is being ignored.
