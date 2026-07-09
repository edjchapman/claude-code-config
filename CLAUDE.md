# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Purpose

This is a configuration repository for Claude Code. It can be consumed two ways:

1. **As a plugin** (recommended): install via `/plugin install claude-code-config` after adding the marketplace. The plugin loader sets `CLAUDE_PLUGIN_DIR` and the hook commands resolve relative to that.
2. **As a symlinked global config** (legacy path, still supported): `scripts/setup-global.sh` symlinks `agents/`, `commands/`, `skills/`, `rules/`, and `settings.json` into `~/.claude/`. Per-project use is via `scripts/setup-project.sh`.

The two modes coexist — hook command paths in `settings.json` use `${CLAUDE_PLUGIN_DIR:-<readlink fallback>}`, so they resolve in both modes without modification.

## Key Scripts

Substitute `<repo>` below with wherever you cloned this repo (commonly
`~/.config/claude-code-config/` or `~/Development/claude-code-config/`).

```bash
# Global setup (creates ~/.claude/agents, commands, skills, rules, and settings.json symlinks)
<repo>/scripts/setup-global.sh

# Project setup (run from target project directory)
<repo>/scripts/setup-project.sh <template> [template2...]
<repo>/scripts/setup-project.sh django --tooling  # + vendor the make-check tooling layer
<repo>/scripts/setup-project.sh --list       # Show templates
<repo>/scripts/setup-project.sh --check django   # Check drift + symlinks
<repo>/scripts/setup-project.sh --status     # Show current config state
<repo>/scripts/setup-project.sh --dry-run django # Preview changes

# Vendor the hard-tooling layer (Makefile, validators, git hooks, CI) into a project.
# Run by `setup-project.sh --tooling`; also works standalone.
<repo>/scripts/install-tooling.sh --hooks [--target DIR] [--dry-run]

# Merge templates (used internally by setup-project.sh)
python3 <repo>/scripts/merge-settings.py <templates-dir> base <type1> [type2...]
python3 <repo>/scripts/merge-mcp.py <mcp-templates-dir> base <type1> [type2...]
```

## Architecture

### Hooks

Hooks are configured in **two places** so the repo works in both consumption modes:

- `settings.json` (`hooks` key) — read by the symlink-global install path. Since `settings.json` is symlinked into `~/.claude/`, hooks are available in all projects.
- `hooks/hooks.json` at the repo root — read by the plugin install path (per [plugin docs](https://code.claude.com/docs/en/plugins.md)). Same shape as `settings.json`'s `hooks` object, wrapped as `{ "hooks": { ... } }`.

**Keep both files in sync** whenever you add or change a hook. Hook scripts themselves live in `scripts/hooks/` and the `${CLAUDE_PLUGIN_DIR:-$(readlink ~/.claude/settings.json | xargs dirname)}` prefix in command paths makes them resolve correctly under either mode.

#### Hook Format

Hooks use string-based matchers (e.g. `"Bash"`, `"Write|Edit"`, `"*"`). See the [official hooks reference](https://code.claude.com/docs/en/hooks.md) for the full schema and the per-event matcher fields.

**Handler types**: a hook entry's `type` can be `command` (shell script), `prompt` (LLM-evaluated yes/no decision — fields: required `prompt` with `$ARGUMENTS` as the hook-input-JSON placeholder; optional `model` (defaults to a fast model), `timeout`, `statusMessage`, `if`, `continueOnBlock`), `agent` (subagent-based verification), `http`, or `mcp_tool`. Command hooks additionally accept `async: true` (run in the background without blocking the turn) and `asyncRewake: true` (background + wake Claude on exit code 2). Repo gotcha: most events support a matcher (filtering on an event-specific field — e.g. `SessionStart` on start reason, `SessionEnd` on exit reason, `PreCompact` on `manual`/`auto`, `SubagentStop` on agent type). The events that **do not** support a matcher and must omit it are: `UserPromptSubmit`, `Stop`, `TaskCompleted`, `PostToolBatch`, `TeammateIdle`, `TaskCreated`, `WorktreeCreate`, `WorktreeRemove`, `MessageDisplay`, `CwdChanged`. Adding a `matcher` field to a no-matcher event is silently ignored per docs.

#### Available hooks

Currently configured in `settings.json`:

- **SessionStart** → `scripts/hooks/session-context.sh`: auto-loads git context (branch, recent commits, dirty files)
- **SessionEnd** → `scripts/hooks/session-end.sh`: appends session summary to `./standups/YYYY-MM-DD-log.md` for later `/standup` consumption
- **PostToolUse (Write|Edit)** → `scripts/hooks/format-on-edit.sh`: auto-formats Python files (ruff) and JS/TS files (prettier); runs `async` so formatting never blocks the turn
- **PostToolUseFailure** → `scripts/hooks/log-tool-failure.sh`: appends failed tool calls to `~/.claude/logs/tool-failures.jsonl` for later pattern analysis
- **PreToolUse (Bash)** → `scripts/hooks/dangerous-cmd-check.sh`: blocks dangerous command patterns (defense-in-depth)
- **PreCompact** → `scripts/hooks/pre-compact-state.sh`: preserves working state before context compaction
- **Stop** → native `type: "prompt"` hook (no script): LLM completeness gate — blocks stopping only when the turn claims implementation work is done while promised tests/linters were skipped or left failing. Evaluated by a fast model on every stop; **enabled by default**. To opt out, delete the `Stop` entry from both `settings.json` and `hooks/hooks.json`.
- **TaskCompleted** → `scripts/hooks/task-completed-chime.sh`: emits a terminal bell when an autonomous task completes

Available but **not configured by default** (opt-in by adding a prompt-type entry to **both** hook files):

- **UserPromptSubmit**: LLM-evaluated check that the user prompt is specific enough
- **SubagentStop**: LLM-evaluated check that a subagent completed its assigned task

Opt-in snippet shape (mirror the configured `Stop` entry, adjusting the event name and prompt):

```json
"UserPromptSubmit": [
  { "hooks": [ { "type": "prompt", "prompt": "<criteria>. Hook input: $ARGUMENTS. When unsure, allow.", "timeout": 30 } ] }
]
```

Prompt-type hooks invoke a fast model on every fire and incur token cost — the Stop gate earns its keep as an always-on quality check; enable the other two deliberately.

CI-only utility (not a runtime hook): `scripts/hooks/check-duplicates.sh` runs from `.github/workflows/validate-config.yml` to fail CI if two agents/skills/commands share a name.

### Settings Keys

Beyond plugins and hooks, `settings.json` currently sets (listed in file order — keep this list in sync when reordering keys):

- **`skillListingBudgetFraction`**: Share of the prompt budget reserved for the skills listing (`0.02` = 2%). In use here but absent from the public settings JSON schema and docs as of this writing — verify its semantics before relying on it.
- **`model`**: Default model alias (`fable`). Briefly removed in `cd66b43` as "deprecated", then restored after verifying the key is still canonical in the settings schema. Accepts aliases (`fable`, `opus`, `sonnet`, `haiku`), full model IDs, and 1M-context forms (e.g. `opus[1m]`).
- **`attribution`**: Git commit/PR attribution text. Both fields are set to empty strings (`commit: ""`, `pr: ""`) to suppress the `Co-Authored-By: Claude` trailer and the "Generated with Claude Code" line on commits **and** PRs — per the schema, the `commit` field covers trailers too, so one empty string handles both. Modern replacement for the deprecated `includeCoAuthoredBy` boolean.
- **`hooks`**: Per-event hook configuration (see Hooks section above)
- **`worktree`**: Worktree-session config. `baseRef: head` branches new worktrees from local HEAD (preserving unpushed commits) instead of `origin/<default>`; `bgIsolation: worktree` blocks Edit/Write in the main checkout until `EnterWorktree` is called.
- **`statusLine`**: Command-based status line showing git branch, dirty count, and PR status
- **`enabledPlugins`**: Plugin enablement map. The checked-in `settings.json` lists only **universal** plugins (no external accounts required). Personal opt-ins (Notion, Figma, frontend-design) live in `settings.personal.json.example`
- **`outputStyle`**: Output style for assistant responses (`Explanatory`; built-ins are `default`, `Explanatory`, `Learning`)
- **`sandbox`**: Sandbox configuration with `enabled` and `autoAllowBashIfSandboxed`
- **`effortLevel`**: Default effort level (e.g. `high`)
- **`agentPushNotifEnabled`**: Push notifications for background agent activity
- **`tui`**: TUI rendering mode (`fullscreen` = flicker-free alt-screen renderer with virtualized scrollback; `default` = classic renderer). Corresponds to the `/tui` command.

Other documented keys that this repo does **not** currently set (available as opt-ins): `env`, `fileSuggestion`, `spinnerVerbs`, `skillOverrides`, `autoMode`, `alwaysThinkingEnabled`, `parentSettingsBehavior`, `autoMemoryDirectory` (custom auto-memory storage dir), `autoMemoryEnabled` (auto-memory on/off, default `true`), `availableModels` / `enforceAvailableModels` (restrict selectable models), `axScreenReader` (screen-reader-friendly output), `fastMode` (faster Opus output, default `false`), `language` (response language preference), `cleanupPeriodDays` (session file retention, default 30), `disableBundledSkills` (hide bundled skills like `/code-review`, `/loop`).

### Skills

Skills use the official nested layout: `skills/<name>/SKILL.md`. Keep frontmatter limited to skill fields such as `name` and `description`; Claude decides when to load a skill from the description, not from a `paths:` block.

Available skills:

- `git-workflow`: Conventional commits, branch naming, PR size, and release workflow guidance
- `testing-patterns`: AAA pattern, factories, mocks, coverage, and test organization
- `security-review`: Input validation, JWT, CSRF, auth, secrets, and security-sensitive routes
- `api-design`: REST conventions, status codes, pagination, schemas, and error formats
- `django-patterns`: Fat models, managers, query optimization, signals, migrations, and admin patterns
- `docker-patterns`: Multi-stage builds, layer caching, Compose files, and container security
- `infrastructure`: Terraform modules, Kubernetes resources, Helm charts, and deployment configuration
- `root-cause-analysis`: Guides incident and bug investigations toward root causes over symptom-level bandaids

### Commands

Commands live as flat Markdown files in `commands/` and are user-invocable as `/<name>`. The five workflow commands below were previously skills; the personal/meta commands (`/standup`, `/status`, `/refinement`, `/eow-review`, `/later`) are documented in the table further down.

Workflow commands:

- `commit.md` (`/commit`): Analyze staged changes and write a conventional commit message
- `pr.md` (`/pr`): Create a pull request with a well-crafted description
- `hotfix.md` (`/hotfix`): Create a hotfix branch with a minimal fix, targeted tests, and PR
- `tdd.md` (`/tdd`): Guide a TDD workflow (Red-Green-Refactor) for a feature or change
- `adr.md` (`/adr`): Create an Architecture Decision Record (Nygard format)

### Rules

Rules are path-scoped code style enforcement files in `rules/`. They use `paths` frontmatter for granular file matching.

Available rules:

- `python-style.md`: Naming, error handling, imports, type hints (`**/*.py`)
- `typescript-style.md`: Naming, error handling, type usage, plus a React-specific section for `.tsx` (`**/*.ts`, `**/*.tsx`)

### Settings Files: Two Purposes

This repo manages three distinct settings files:

| File                             | Purpose                                                             | Distribution                                            | Source                            |
| -------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------- | --------------------------------- |
| `settings.json`                  | **Universal** plugin enablement + hooks (no external auth required) | **Symlinked** from repo root                            | Canonical copy in repo            |
| `settings.personal.json.example` | Opt-in fragment for plugins requiring external accounts/auth        | **Copied** by hand into `~/.claude/settings.local.json` | Template in repo                  |
| `settings.local.json`            | Bash permissions + any personal plugin opt-ins                      | **Generated** per-project + hand-edited globally        | Merged from `settings-templates/` |

**Why split universal vs personal plugins?** The repo is consumable by anyone (via plugin install or symlink). Auto-enabling Notion/Figma/etc. for someone who has no account or doesn't use those tools is surprising. `settings.json` carries only plugins that work without external accounts (github, pr-review-toolkit, feature-dev, code-simplifier, playwright, pyright-lsp, typescript-lsp, document-skills). Personal opt-ins (`Notion`, `figma`, `frontend-design`) live in `settings.personal.json.example` and are merged into the maintainer's `~/.claude/settings.local.json` by hand.

**Note on merge semantics**: Claude Code's documented behavior for `enabledPlugins` across settings layers is not explicitly spelled out in the docs (the example given covers scalars, where the higher-precedence layer wins). If you observe universal plugins being shadowed when the example is active, include the universal list alongside the personal entries in your local file. See [Claude Code settings docs](https://code.claude.com/docs/en/settings.md) for precedence rules.

### Settings Template System

Templates in `settings-templates/` are JSON files defining Claude Code permissions. The merge system:

1. Always includes `base.json` first (git, gh CLI, file operations)
2. Adds requested templates in order (django, react, etc.)
3. Merges permissions with precedence: **deny > allow**
4. Outputs combined `settings.local.json`

Available templates (14 total):

- **Base**: `base.json` (always included)
- **Backend stacks**: `django.json`, `fastapi.json`, `go.json`, `java.json`, `node.json`, `python.json`, `rust.json`
- **Frontend stacks**: `nextjs.json`, `react.json`
- **Platform / infra**: `aws.json`, `docker.json`, `kubernetes.json`, `terraform.json`

Template structure:

```json
{
  "_source": "template-name",
  "_version": 1,
  "permissions": {
    "allow": ["Bash(command:*)"],
    "deny": ["Bash(dangerous:*)"]
  }
}
```

Bump `_version` when a template's permission set changes meaningfully — the value isn't used by the merge logic but signals drift to humans reviewing diffs.

### MCP Template System

MCP templates in `mcp-templates/` define MCP server configurations per project type. The merge system:

1. Always includes `base.json` first (empty by default — MCP is opt-in)
2. Adds MCP servers from matching type templates
3. Outputs combined `.mcp.json` in the project root

Available MCP templates:

- `base.json`: Empty (MCP servers are opt-in)
- `django.json` (`_version: 2`): PostgreSQL MCP server (`@modelcontextprotocol/server-postgres`)
- `nextjs.json`: PostgreSQL MCP server
- `fastapi.json`: PostgreSQL MCP server
- `python.json` (`_version: 1`): SQLite MCP server (`mcp-server-sqlite-npx`) for generic Python local dev
- `node.json` (`_version: 1`): SQLite MCP server (`mcp-server-sqlite-npx`) for generic Node local dev
- `aws.json` (`_version: 1`): AWS Infrastructure-as-Code MCP server (`awslabs.aws-iac-mcp-server`) for CloudFormation/CDK validation, `cfn-guard` compliance, and deployment troubleshooting. Runs via `uvx` (Python/PyPI), not `npx` — needs the `uv` package manager plus AWS credentials (`AWS_PROFILE`/`AWS_REGION`). The deprecated `awslabs.terraform-mcp-server` is deliberately excluded; HashiCorp's official Terraform MCP server has superseded it.

Stacks without an MCP template (Go, Rust, Java, Kubernetes, Terraform) fall through to `base.json` (empty); add MCP servers manually in the project's generated `.mcp.json` when needed. The frameworks with web/DB context default to PostgreSQL; generic Python/Node templates use SQLite because there's no shared external DB assumption. The `aws` template is the lone infra MCP server — it's `uvx`-based rather than `npx`-based, so verify against PyPI (confirmed `awslabs.aws-iac-mcp-server` published at template creation time) rather than the npm registry. Verify each template's package before relying on it — versions move (npm search confirmed `mcp-server-sqlite-npx@0.8.0` exists at template creation time).

Playwright is now provided as a first-class plugin (`playwright@claude-plugins-official`,
enabled in `settings.json`), not via an MCP template, so React projects do not
generate a `.mcp.json` from this repo by default.

**Environment Variables**: Variables like `${DATABASE_URL}` are expanded at Claude Code runtime.
Ensure required variables are set in your shell or `.envrc` before launching Claude Code.

### CLI Scripts

Headless Claude Code scripts in `scripts/cli/` for automation:

- `review-changes.sh`: Review uncommitted changes for bugs, security, quality
- `explain-error.sh`: Pipe errors to Claude for explanation (`cmd 2>&1 | explain-error.sh`)
- `daily-report.sh`: Summarize last 24h of git activity
- `review-pr.sh <number>`: Headless PR review

### Agent Definitions

Agents in `agents/` are Markdown files with YAML frontmatter:

- `name`: Agent identifier (used as `@agent-name`)
- `description`: When Claude should invoke this agent (include examples)
- `model`: `opus` for complex reasoning, `sonnet` for pattern-based, `haiku` for highly structured / data-plumbing
- `tools` (optional): Restrict the agent to a specific tool subset
- `color` (optional): UI hint for the agent's display colour
- `permissionMode` (optional): Override the subagent's permission mode (e.g. `plan` starts the agent in plan mode for spec/review work that should not edit until approved)

### Skill Definitions

Skills use the official nested layout: each skill is a directory `skills/<name>/SKILL.md` with YAML frontmatter. **Canonical fields** (per the [Claude Code skills docs](https://code.claude.com/docs/en/skills)):

- `name`: Skill identifier (used as `/skill-name`)
- `description`: Rich description shown in the skill picker AND used by Claude to decide when to load the skill. Pattern: `"<what it does>. Use when <user trigger phrasing>."` — Claude matches this against the conversation, not against file globs.
- `argument-hint` (optional): Hint shown in autocomplete for `$ARGUMENTS`
- `allowed-tools` (optional): Tools pre-approved while the skill is active (space/comma-separated or YAML list)
- `disable-model-invocation` (optional): Set `true` for user-only invocation (Claude won't auto-fire)
- `user-invocable` (optional): Set `false` to hide from the `/` picker (background knowledge only)
- `model`, `effort` (optional): Per-skill model/effort overrides

**Do not use** `when_to_use:`, `globs:`, or `paths:` — these are non-canonical for skills and silently ignored. Skills are loaded from `description:`, not file globs; merge any "when to use" content into `description:`. (Path-scoped file matching lives in `rules/`, which do use `paths:`.)

### Command Definitions

Per the official docs, custom commands and skills share the same frontmatter contract: `commands/foo.md` and `skills/foo/SKILL.md` both create `/foo`. We keep `commands/` for user-invocable workflows and personal/meta commands (`/commit`, `/pr`, `/hotfix`, `/tdd`, `/adr`, plus `/standup`, `/status`, `/refinement`, `/eow-review`, `/later`), and `skills/` for domain knowledge Claude loads automatically from a skill's `description:`.

## Commands, Agents, and Skills — when to use each

The three primitives serve different purposes; picking the right one keeps the agent/skill picker uncluttered.

| Use a...                  | When                                                                                                                        | Example in this repo                                                                                          |
| ------------------------- | --------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| **Skill** (`skills/`)     | Domain knowledge you want Claude to load automatically based on the conversation (matched from the skill's `description:`)  | `django-patterns` (loads when editing Django models/views), `security-review` (loads on auth/middleware work) |
| **Command** (`commands/`) | Personal/meta workflow that should only fire when you explicitly ask                                                        | `/standup`, `/eow-review`, `/later`                                                                           |
| **Agent** (`agents/`)     | Specialist `@agent-name` task with a forked context — deep, single-domain work that shouldn't pollute the main conversation | `@bug-resolver`, `@migration-engineer`, `@security-auditor`                                                   |

Rule of thumb: if the action is **domain knowledge Claude should load automatically** (patterns for Django models, security-sensitive code), it wants to be a skill. If the action is a **user-invocable workflow or personal/meta task** ("commit my work", "open a PR", "give me a standup summary"), it wants to be a command. If the action is **scoped expertise that benefits from isolation** ("audit this for security"), it wants to be an agent.

## Plugin vs custom — what stays in this repo

Several enabled plugins (visible in `settings.json`'s `enabledPlugins`) overlap with what custom agents/commands could provide. The rule applied during the modernization sweep:

> **Retire custom only when the plugin fully subsumes its purpose AND the plugin is already enabled.** Borderline cases stay custom.

Currently retired in favor of plugins:

| Retired                                            | Replaced by                                                                                   |
| -------------------------------------------------- | --------------------------------------------------------------------------------------------- |
| `agents/code-reviewer.md`                          | `pr-review-toolkit:code-reviewer` (depth) + `feature-dev:code-reviewer` (confidence-filtered) |
| `agents/spec-writer.md`                            | `feature-dev:code-architect`                                                                  |
| `commands/review.md`                               | bundled `/review`                                                                             |
| `commands/security-scan.md`                        | bundled `/security-review`                                                                    |
| `commands/deps.md` (delegation wrapper)            | `@dependency-manager` (the agent auto-detects npm/pip/uv/poetry/go/cargo)                     |
| `commands/coverage-report.md` (delegation wrapper) | `@test-engineer` (the agent auto-detects Django/Jest/Vitest and analyzes coverage gaps)       |

Kept custom because no enabled plugin fully covers them:

- `@bug-resolver`, `@ci-debugger`, `@database-architect`, `@dependency-manager`, `@devops-engineer`, `@documentation-writer`, `@e2e-playwright-engineer`, `@git-helper`, `@migration-engineer`, `@performance-engineer`, `@pr-review-bundler`, `@refactoring-engineer`, `@security-auditor`, `@test-engineer`
- `/commit`, `/pr`, `/hotfix`, `/tdd`, `/adr`, `/standup`, `/status`, `/refinement`, `/eow-review`, `/later`

If you enable a new plugin and it overlaps with one of the kept-custom items, re-apply the rule.

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

## Self-Extension Guide

When extending this repo (adding a new agent / skill / command / hook / template), copy the most-similar exemplar rather than writing frontmatter from scratch. The exemplars below have been verified against the canonical Claude Code docs.

### Add an agent

- **Where**: `agents/<kebab-name>.md`
- **Required frontmatter**: `name`, `description` (include `<example>` blocks for when to invoke)
- **Optional**: `model` (`opus`/`sonnet`/`haiku`), `tools`, `color`, `permissionMode`
- **Model heuristic**: `opus` for complex reasoning (bug-resolver, security-auditor), `sonnet` for pattern-based work (test-engineer, documentation-writer), `haiku` for highly-structured data-plumbing
- **Exemplar**: [`agents/bug-resolver.md`](agents/bug-resolver.md) — opus, rich description with examples

### Add a skill (domain knowledge, loaded by description)

- **Where**: `skills/<kebab-name>/SKILL.md` (nested layout — one directory per skill)
- **Required frontmatter**: `name`, `description` — write description as `"<what it does>. Use when <user trigger phrasing>."` so Claude loads it from the conversation. Skills are matched on `description:`, not on file globs.
- **Optional**: `argument-hint`, `allowed-tools`, `disable-model-invocation: true`, `user-invocable: false`, `model`, `effort`
- **Exemplar**: [`skills/django-patterns/SKILL.md`](skills/django-patterns/SKILL.md)
- **Don't**: use `when_to_use:`, `globs:`, or `paths:` (non-canonical for skills — merge intent into `description:`). Former workflow skills (`/commit`, `/pr`, `/hotfix`, `/tdd`, `/adr`) now live in `commands/` — see "Add a command" below.

### Add a command

- **Where**: `commands/<kebab-name>.md`
- **Required frontmatter**: `description` (and optionally `argument-hint`)
- **When to choose this over a skill**: only for personal/meta workflows that you never want Claude to auto-invoke. For everything else, prefer a skill — they're a strict superset.
- **Exemplar**: [`commands/eow-review.md`](commands/eow-review.md)

### Add a hook

- **Prompt-type hooks need no script**: for LLM-evaluated gates, add a `{ "type": "prompt", "prompt": "..." }` entry directly to both hook files (exemplar: the configured `Stop` hook). The steps below cover command-type hooks.
- **Script location**: `scripts/hooks/<name>.sh` (set `chmod +x`, include `#!/usr/bin/env bash`)
- **Wire-up — two files**: add the entry to **both** `settings.json` (under `hooks.<EventName>`) and `hooks/hooks.json` (under `hooks.<EventName>` inside the top-level `{"hooks": {...}}` wrapper). Same shape in both. Use a `command` value of `"${CLAUDE_PLUGIN_DIR:-$(readlink ~/.claude/settings.json | xargs dirname)}/scripts/hooks/<name>.sh"` so it resolves in both plugin and symlink-global modes.
- **Matcher rules**: most events support a `matcher` field — tool events filter on tool name (e.g. `"Bash"`, `"Edit|Write"`); other events filter on event-specific fields (e.g. `SessionStart` on start reason, `SessionEnd` on exit reason, `SubagentStop` on agent type). Events that **don't** support matchers and must omit the field: `UserPromptSubmit`, `Stop`, `TaskCompleted`, `PostToolBatch`, `TeammateIdle`, `TaskCreated`, `WorktreeCreate`, `WorktreeRemove`, `MessageDisplay`, `CwdChanged`. See [hooks reference](https://code.claude.com/docs/en/hooks.md) for the full per-event schema.
- **Exemplar wire-up**: any current entry in `settings.json` or `hooks/hooks.json` under `hooks.*`

### Add a settings template

- **Where**: `settings-templates/<stack>.json`
- **Schema**: `_source`, `_version`, `permissions.allow`, `permissions.deny`
- **Precedence**: `deny` beats `allow` during merge — use deny lists for stack-specific footguns (e.g. `terraform.json` denying `terraform destroy:*`)
- **Exemplar**: [`settings-templates/django.json`](settings-templates/django.json)

### After extending

Run the validation suite locally before pushing:

```bash
python -m json.tool settings.json > /dev/null   # JSON sanity
scripts/hooks/check-duplicates.sh               # No agent/skill/command name collisions
python3 scripts/check-hooks-sync.py             # settings.json hooks == hooks/hooks.json hooks
```

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

## Tooling Troubleshooting

If a tool or integration isn't working (e.g., MCP server, browser extension, external API), pivot after 2 failed attempts rather than retrying across the entire session. Suggest an alternative approach or escalate to the user. The cost of continued retrying far exceeds the cost of asking for help.

## Commit Messages

Follow conventional commits:

```
feat(agents): add kubernetes-helper agent
fix(scripts): handle spaces in paths
docs: update template documentation
```
