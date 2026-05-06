# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Purpose

This is a configuration repository for Claude Code. It provides reusable agents, commands, and permission templates that can be symlinked to `~/.claude/` (global) or `.claude/` (per-project) directories. Changes here propagate to all linked projects automatically.

## Key Scripts

```bash
# Global setup (creates ~/.claude/agents, commands, skills, rules, and settings.json symlinks)
./scripts/setup-global.sh

# Project setup (run from target project directory)
~/Development/claude-code-config/scripts/setup-project.sh <template> [template2...]
~/Development/claude-code-config/scripts/setup-project.sh --list       # Show templates
~/Development/claude-code-config/scripts/setup-project.sh --check django   # Check drift + symlinks
~/Development/claude-code-config/scripts/setup-project.sh --status     # Show current config state
~/Development/claude-code-config/scripts/setup-project.sh --dry-run django # Preview changes

# Merge templates (used internally by setup-project.sh)
python3 scripts/merge-settings.py <templates-dir> base <type1> [type2...]
python3 scripts/merge-mcp.py <mcp-templates-dir> base <type1> [type2...]
```

## Architecture

### Hooks

Hooks are configured in `settings.json` under the `"hooks"` key. Since `settings.json` is symlinked globally, hooks are available in all projects. Hook scripts live in `scripts/hooks/` and are referenced via `readlink` to resolve the repo path from the symlink.

#### Hook Format

Hooks use string-based matchers (not object-based). The correct format:

```json
{
  "hooks": {
    "EventName": [
      {
        "matcher": "ToolPattern",
        "hooks": [{"type": "command", "command": "your-command"}]
      }
    ]
  }
}
```

**Matcher patterns:**

- Simple string: `"Bash"` matches only Bash tool
- Regex: `"Write|Edit"` or `"Notebook.*"`
- Match all: `"*"` or `""`
- Omit matcher for events that don't use it (SessionStart, Stop, PreCompact, UserPromptSubmit, SubagentStop)

**Example:**

```json
{
  "PostToolUse": [
    {
      "matcher": "Write|Edit",
      "hooks": [{"type": "command", "command": "./format.sh"}]
    }
  ],
  "SessionStart": [
    {
      "hooks": [{"type": "command", "command": "./load-context.sh"}]
    }
  ]
}
```

#### Available hooks

- **SessionStart**: Auto-loads git context (branch, recent commits, dirty files)
- **Setup (init)**: Detects project type and suggests configuration
- **UserPromptSubmit**: LLM-evaluated check that user prompt is specific enough to act on
- **PostToolUse (Write|Edit)**: Auto-formats Python files (ruff) and JS/TS files (prettier)
- **PreToolUse (Bash)**: Blocks dangerous command patterns (defense-in-depth)
- **Stop**: LLM-evaluated completeness check (tests run? linters run? TODOs left?)
- **SubagentStop**: LLM-evaluated check that subagent completed its assigned task fully
- **PreCompact**: Preserves working state before context compaction

### Settings Keys

Beyond plugins and hooks, `settings.json` includes:

- **`env`**: Environment variables for Claude Code sessions (e.g., `MAX_THINKING_TOKENS`)
- **`attribution`**: Auto-appended commit trailer (e.g., `Co-Authored-By` line)
- **`statusLine`**: Command-based status line showing git branch, dirty count, and PR status
- **`fileSuggestion`**: Command-based file suggestion using `git ls-files`
- **`sandbox`**: Sandbox configuration with `autoAllowBashIfSandboxed`
- **`spinnerVerbs`**: Custom spinner verbs appended to defaults

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
- `typescript-style.md`: Naming, error handling, type usage (`**/*.ts`, `**/*.tsx`)
- `react-style.md`: Component structure, props, hooks, state (`**/*.tsx`)

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
- `model`: `opus` for complex reasoning, `sonnet` for pattern-based tasks

### Command Definitions

Commands in `commands/` are Markdown files where the filename becomes the slash command (e.g., `commit.md` → `/commit`).

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
