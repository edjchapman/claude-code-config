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
<repo>/scripts/setup-project.sh --list       # Show templates
<repo>/scripts/setup-project.sh --check django   # Check drift + symlinks
<repo>/scripts/setup-project.sh --status     # Show current config state
<repo>/scripts/setup-project.sh --dry-run django # Preview changes

# Merge templates (used internally by setup-project.sh)
python3 <repo>/scripts/merge-settings.py <templates-dir> base <type1> [type2...]
python3 <repo>/scripts/merge-mcp.py <mcp-templates-dir> base <type1> [type2...]
```

## Architecture

### Hooks

Hooks are configured in `settings.json` under the `"hooks"` key. Since `settings.json` is symlinked globally, hooks are available in all projects. Hook scripts live in `scripts/hooks/` and are referenced via `readlink` to resolve the repo path from the symlink.

#### Hook Format

Hooks use string-based matchers (e.g. `"Bash"`, `"Write|Edit"`, `"*"`). See
the official Claude Code hooks docs for the full schema. Repo gotcha: omit
`matcher` for events that don't dispatch on a tool name (`SessionStart`,
`PreCompact`, `Stop`, `SubagentStop`, `UserPromptSubmit`).

#### Available hooks

Currently configured in `settings.json`:

- **SessionStart**: Auto-loads git context (branch, recent commits, dirty files)
- **PostToolUse (Write|Edit)**: Auto-formats Python files (ruff) and JS/TS files (prettier)
- **PostToolUseFailure**: Appends failed tool calls to `~/.claude/logs/tool-failures.jsonl` for later pattern analysis
- **PreToolUse (Bash)**: Blocks dangerous command patterns (defense-in-depth)
- **PreCompact**: Preserves working state before context compaction
- **TaskCompleted**: Emits a terminal bell when an autonomous task completes

Available but **not configured by default** (opt-in by adding to `settings.json`):

- **UserPromptSubmit**: LLM-evaluated check that the user prompt is specific enough
- **Stop**: LLM-evaluated completeness check (tests run? linters run? TODOs left?)
- **SubagentStop**: LLM-evaluated check that a subagent completed its assigned task

The three opt-in hooks invoke an LLM on every fire and incur token cost — enable
deliberately, not by default.

### Settings Keys

Beyond plugins and hooks, `settings.json` currently sets:

- **`model`**: Default model (e.g. `opus[1m]` for Opus with 1M context)
- **`hooks`**: Per-event hook configuration (see Hooks section above)
- **`statusLine`**: Command-based status line showing git branch, dirty count, and PR status
- **`enabledPlugins`**: Plugin enablement map (GitHub, Notion, Figma, LSPs, etc.)
- **`sandbox`**: Sandbox configuration with `enabled` and `autoAllowBashIfSandboxed`
- **`effortLevel`**: Default effort level (e.g. `high`)
- **`agentPushNotifEnabled`**: Push notifications for background agent activity

Other documented keys that this repo does **not** currently set (available as opt-ins): `env`, `attribution`, `fileSuggestion`, `spinnerVerbs`, `worktree`, `outputStyle`, `skillListingBudgetFraction`, `skillOverrides`, `autoMode`, `alwaysThinkingEnabled`, `parentSettingsBehavior`.

### Skills

Skills are domain knowledge documents in `skills/` that auto-activate based on file glob patterns. Unlike agents (explicitly invoked), skills provide passive context when relevant files are touched.

Available skills:

- `git-workflow.md`: Conventional commits, branch naming, PR size (`.git/**`)
- `testing-patterns.md`: AAA pattern, factories, coverage (`**/test_*.py`, `**/*_test.py`, `**/*.test.ts`, `**/*.test.tsx`, `**/*.spec.ts`, `**/*.spec.tsx`)
- `security-review.md`: Input validation, JWT, CSRF, auth (`**/auth/**`, `**/middleware/**`, `**/security/**`, `**/routes/**`)
- `api-design.md`: REST conventions, status codes, pagination (`**/views/**`, `**/api/**`, `**/routes/**`, `**/controllers/**`, `**/endpoints/**`)
- `django-patterns.md`: Fat models, managers, query optimization, signals (`**/models.py`, `**/views.py`, `**/managers.py`, `**/signals.py`, etc.)
- `docker-patterns.md`: Multi-stage builds, layer caching, security (`**/Dockerfile`, `**/docker-compose*.yml`, `**/.dockerignore`)
- `infrastructure.md`: Terraform modules, K8s resources, Helm charts (`**/*.tf`, `**/k8s/**`, `**/helm/**`)
- `root-cause-analysis.md`: Guides bug fixes toward root causes over symptom-level bandaids (`**/*.py`)

### Rules

Rules are path-scoped code style enforcement files in `rules/`. They use `paths` frontmatter for granular file matching.

Available rules:

- `python-style.md`: Naming, error handling, imports, type hints (`**/*.py`)
- `typescript-style.md`: Naming, error handling, type usage, plus a React-specific section for `.tsx` (`**/*.ts`, `**/*.tsx`)

### Settings Files: Two Purposes

This repo manages two distinct settings files:

| File | Purpose | Distribution | Source |
|------|---------|--------------|--------|
| `settings.json` | Plugin enablement (GitHub, Notion, LSPs, etc.) | **Symlinked** from repo root | Canonical copy in repo |
| `settings.local.json` | Bash permissions (what commands Claude can run) | **Generated** per-project | Merged from `settings-templates/` |

**Why separate?**

- **Plugins** (`settings.json`): Personal preference, same across all projects, updated by adding plugins to repo
- **Permissions** (`settings.local.json`): Project-specific, varies by tech stack (Django vs React vs Go)

Both files coexist in `.claude/` directories and serve different purposes.

### Settings Template System

Templates in `settings-templates/` are JSON files defining Claude Code permissions. The merge system:

1. Always includes `base.json` first (git, gh CLI, file operations)
2. Adds requested templates in order (django, react, etc.)
3. Merges permissions with precedence: **deny > allow**
4. Outputs combined `settings.local.json`

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

### MCP Template System

MCP templates in `mcp-templates/` define MCP server configurations per project type. The merge system:

1. Always includes `base.json` first (empty by default — MCP is opt-in)
2. Adds MCP servers from matching type templates
3. Outputs combined `.mcp.json` in the project root

Available MCP templates:

- `base.json`: Empty (MCP servers are opt-in)
- `django.json`: PostgreSQL MCP server
- `nextjs.json`: PostgreSQL MCP server
- `fastapi.json`: PostgreSQL MCP server

Stacks without an MCP template (Node, Python, Go, Rust, Java, Kubernetes, Terraform) fall through to `base.json` (empty); add MCP servers manually in the project's generated `.mcp.json` when needed. Only PostgreSQL is templated because it's the one canonical reference server with a stable npm package this repo has confirmed working — other MCP servers can be added per-project once you've validated the package name and connection.

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

Skills in `skills/` are Markdown files with YAML frontmatter:

- `name`: Skill identifier (used as `/skill-name`)
- `description`: One-line summary shown in the skill picker
- `when_to_use`: Plain-English trigger description; Claude self-invokes when the conversation matches
- `globs` (optional): Glob patterns that auto-activate the skill when files match (passive domain knowledge use case)
- `argument-hint` (optional): Hint shown in autocomplete for `$ARGUMENTS`
- `allowed-tools` (optional): Restrict tools available while the skill is active

### Command Definitions

Commands in `commands/` are Markdown files where the filename becomes the slash command (e.g., `standup.md` → `/standup`). Commands are user-invoke only — Claude does not auto-invoke them. Use a skill with `when_to_use` instead when you want auto-invocation.

## Commands, Agents, and Skills — when to use each

The three primitives serve different purposes; picking the right one keeps the agent/skill picker uncluttered.

| Use a... | When | Example in this repo |
|---|---|---|
| **Skill** (`skills/`) | Workflow you want Claude to auto-invoke based on the conversation, or domain knowledge that auto-activates on matching files | `/commit` (auto-fires on "commit my staged work"), `django-patterns` (auto-activates on `models.py`) |
| **Command** (`commands/`) | Personal/meta workflow that should only fire when you explicitly ask | `/standup`, `/eow-review`, `/later` |
| **Agent** (`agents/`) | Specialist `@agent-name` task with a forked context — deep, single-domain work that shouldn't pollute the main conversation | `@bug-resolver`, `@migration-engineer`, `@security-auditor` |

Rule of thumb: if the action is **conversational** ("commit my work", "open a PR"), it wants to be a skill. If the action is **on-demand and personal** ("give me a standup summary"), it wants to be a command. If the action is **scoped expertise that benefits from isolation** ("audit this for security"), it wants to be an agent.

## Plugin vs custom — what stays in this repo

Several enabled plugins (visible in `settings.json`'s `enabledPlugins`) overlap with what custom agents/commands could provide. The rule applied during the modernization sweep:

> **Retire custom only when the plugin fully subsumes its purpose AND the plugin is already enabled.** Borderline cases stay custom.

Currently retired in favor of plugins:

| Retired | Replaced by |
|---|---|
| `agents/code-reviewer.md` | `pr-review-toolkit:code-reviewer` (depth) + `feature-dev:code-reviewer` (confidence-filtered) |
| `agents/spec-writer.md` | `feature-dev:code-architect` |
| `commands/review.md` | bundled `/review` |
| `commands/security-scan.md` | bundled `/security-review` |

Kept custom because no enabled plugin fully covers them:

- `@bug-resolver`, `@ci-debugger`, `@database-architect`, `@dependency-manager`, `@devops-engineer`, `@documentation-writer`, `@e2e-playwright-engineer`, `@git-helper`, `@migration-engineer`, `@performance-engineer`, `@pr-review-bundler`, `@refactoring-engineer`, `@security-auditor`, `@test-engineer`
- `/commit`, `/pr`, `/hotfix`, `/tdd`, `/adr`, `/standup`, `/deps`, `/coverage-report`, `/refinement`, `/eow-review`, `/later`

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
