# Claude Code Config

Reusable agents, commands, and permission templates for [Claude Code](https://claude.ai/code).

## Why This Exists

Claude Code stores configuration in `~/.claude/` (global) and `.claude/` (per-project). Managing this across multiple projects and machines becomes tedious:

- **Agents** need to be copied to each project
- **Commands** are duplicated everywhere
- **Permission templates** drift between projects
- **New machines** require manual setup

This repo solves that by providing:
- A **single source of truth** for your Claude Code configuration
- **Symlinks** so updates propagate everywhere automatically
- **Composable templates** for different project types
- **Hooks** for auto-formatting, safety checks, and notifications
- **Skills** for passive domain knowledge activation
- **Setup scripts** that work on any machine

## Quick Start

```bash
# 1. Clone (or fork if you want to customize)
git clone https://github.com/edjchapman/claude-code-config.git ~/claude-code-config

# 2. Set up global config
~/claude-code-config/scripts/setup-global.sh

# 3. Set up a project (from your project directory)
cd ~/my-django-project
~/Development/claude-code-config/scripts/setup-project.sh django

# 4. Start using Claude Code - agents and commands are now available
claude
```

**Tip:** Add an alias for easier use:
```bash
# Add to ~/.bashrc or ~/.zshrc
alias claude-setup='~/Development/claude-code-config/scripts/setup-project.sh'

# Then use it like:
claude-setup django react
```

## What Gets Created

**Global setup** (`setup-global.sh`) creates symlinks in `~/.claude/`:
```
~/.claude/
├── agents       -> ~/claude-code-config/agents
├── commands     -> ~/claude-code-config/commands
├── skills       -> ~/claude-code-config/skills
└── settings.json -> ~/claude-code-config/settings.json
```

**Project setup** (`setup-project.sh`) creates in your project:
```
your-project/.claude/
├── agents              -> ~/claude-code-config/agents
├── commands            -> ~/claude-code-config/commands
├── skills              -> ~/claude-code-config/skills
├── settings.json       -> ~/claude-code-config/settings.json
└── settings.local.json (generated from templates)
```

### Understanding Settings Files

- **`settings.json`** (symlinked): Plugin enablement, hooks configuration, and model selection
- **`settings.local.json`** (generated): Permissions - what bash commands and tools Claude can use in your project

## Fork or Clone?

| Approach | When to Use |
|----------|-------------|
| **Clone** | You want to use as-is, or contribute improvements back |
| **Fork** | You want to customize agents/commands for your own workflow |

If you fork, you can still pull updates from upstream:
```bash
git remote add upstream https://github.com/edjchapman/claude-code-config.git
git fetch upstream
git merge upstream/main
```

## Available Templates

Use one or combine multiple:

```bash
~/Development/claude-code-config/scripts/setup-project.sh python          # Python project
~/Development/claude-code-config/scripts/setup-project.sh django          # Django
~/Development/claude-code-config/scripts/setup-project.sh django react    # Full-stack
~/Development/claude-code-config/scripts/setup-project.sh go              # Go project
~/Development/claude-code-config/scripts/setup-project.sh node            # Node.js
~/Development/claude-code-config/scripts/setup-project.sh terraform       # Infrastructure
~/Development/claude-code-config/scripts/setup-project.sh all             # ALL templates
```

| Template | What It Allows |
|----------|----------------|
| `all` | All templates below combined |
| `base` | Git, GitHub CLI, file operations, WebSearch *(always included)* |
| `python` | pytest, mypy, ruff, black, isort, flake8, pylint, bandit, pre-commit, pip, uv, poetry |
| `django` | Django manage.py commands, docker compose, make, uv run (pytest, flake8, basedpyright) |
| `react` | npm, yarn, pnpm, vitest, playwright, TypeScript, eslint, prettier |
| `node` | npm, yarn, pnpm, vitest, jest, mocha, eslint, prettier, tsc, bun |
| `nextjs` | Next.js dev/build/lint, Vercel CLI, npm/yarn/pnpm, vitest, playwright |
| `fastapi` | uvicorn, alembic, pytest, ruff, mypy, uv, poetry, docker compose |
| `go` | go build/test/run, golangci-lint, staticcheck, dlv, mockgen, wire |
| `terraform` | terraform fmt/validate/plan/init |

## Available Agents

Invoke with `@agent-name` in Claude Code:

| Agent | What It Does | Model |
|-------|--------------|-------|
| `@bug-resolver` | Systematic debugging, root cause analysis | opus |
| `@ci-debugger` | CI/CD failure investigation, flaky tests | opus |
| `@code-reviewer` | General code review for any language | opus |
| `@database-architect` | Schema design, migration planning, query optimization | opus |
| `@dependency-manager` | Dependency audit, outdated packages, license checks | sonnet |
| `@devops-engineer` | Infrastructure, CI/CD pipelines, containers | opus |
| `@django-code-reviewer` | Django security/performance review, N+1 detection | opus |
| `@documentation-writer` | README, API docs, ADRs, onboarding guides | sonnet |
| `@e2e-playwright-engineer` | Create and debug Playwright E2E tests | opus |
| `@git-helper` | Complex git: rebase, conflicts, recovery | sonnet |
| `@migration-engineer` | Database migrations, framework upgrades, zero-downtime | opus |
| `@performance-engineer` | Profiling, bottleneck analysis, optimization | opus |
| `@pr-review-bundler` | Bundle PR reviews into markdown | opus |
| `@refactoring-engineer` | Systematic, safe refactoring | opus |
| `@security-auditor` | Security audit, OWASP, dependency vulnerabilities | opus |
| `@spec-writer` | Technical specs and planning docs | opus |
| `@test-engineer` | Create unit and integration tests | sonnet |

**Model notes:**
- **Opus** = complex reasoning, security reviews, planning (higher cost)
- **Sonnet** = pattern-based tasks, faster, lower cost

## Available Commands

Invoke with `/command` in Claude Code:

| Command | What It Does |
|---------|--------------|
| `/commit` | Analyze staged changes, generate commit message |
| `/pr` | Create PR with auto-generated description |
| `/review` | Review changes before committing |
| `/standup` | Summarize last 24h of git activity |
| `/explain` | Explain code at a specific location |
| `/lint` | Run all project linters |
| `/tdd` | TDD workflow: write failing test, implement, refactor |
| `/hotfix` | Guided hotfix: branch from main, minimal fix, targeted tests, PR |
| `/deps` | Dependency audit: vulnerabilities, outdated packages, update plan |
| `/adr` | Create Architecture Decision Record (Nygard format) |
| `/context` | Refresh context: branch, commits, open PRs, project status |
| `/format-release-notes` | Format GitHub release notes |
| `/coverage-report` | Analyze test coverage and identify gaps |
| `/generate-changelog` | Generate changelog from commits since last tag |
| `/refinement` | Prepare technical analysis for backlog refinement |
| `/security-scan` | Run security audit on the codebase |

## Directory Structure

```
claude-code-config/
├── agents/                  # Agent definitions (markdown)
├── commands/                # Slash commands (markdown)
├── skills/                  # Auto-activating domain knowledge (markdown)
├── settings-templates/      # Permission templates (JSON)
├── settings.json            # Plugin config + hooks (symlinked globally)
├── scripts/
│   ├── setup-global.sh      # One-time machine setup
│   ├── setup-project.sh     # Per-project setup
│   ├── merge-settings.py    # Template merger
│   └── hooks/               # Hook scripts referenced by settings.json
│       ├── session-context.sh
│       ├── format-python.sh
│       ├── format-js.sh
│       ├── dangerous-cmd-check.sh
│       ├── pre-compact-state.sh
│       └── notify-permission.sh
└── web_shortcuts/           # Web workflow prompts (for claude.ai web interface)
```

## Hooks

Hooks are configured in `settings.json` and run automatically at key points in the Claude Code lifecycle. Since `settings.json` is symlinked globally, hooks work in all projects.

| Hook | Trigger | What It Does |
|------|---------|--------------|
| SessionStart | New session | Outputs git branch, recent commits, and dirty files |
| PostToolUse (Write/Edit) | After file edits | Auto-formats Python (ruff) and JS/TS (prettier) |
| PreToolUse (Bash) | Before commands | Blocks dangerous patterns (`rm -rf /`, `dd`, etc.) |
| Stop | Session end | LLM checks: tests run? linters run? TODOs left? |
| PreCompact | Before compaction | Saves working state (branch, staged files, recent commits) |
| Notification | Permission needed | Sends macOS desktop notification |

Hook scripts live in `scripts/hooks/` and only run when the required tools are available (e.g., `ruff`, `prettier`).

## Skills

Skills are domain knowledge documents that auto-activate when you touch matching files. They provide passive guidance without explicit invocation.

| Skill | Activates On | What It Covers |
|-------|-------------|----------------|
| `coding-standards` | `*.py`, `*.ts`, `*.tsx` | Naming, function length, error handling |
| `git-workflow` | `.git/**` | Conventional commits, branch naming, PR size |
| `testing-patterns` | `test_*.py`, `*.test.ts` | AAA pattern, factories, coverage |
| `security-review` | `auth/**`, `middleware/**` | Input validation, JWT, CSRF, secrets |
| `api-design` | `views/**`, `api/**`, `serializers/**` | REST conventions, status codes, pagination |

### Web Shortcuts

The `web_shortcuts/` directory contains prompts designed for use with the Claude web interface (claude.ai) rather than Claude Code CLI. These integrate with external services like Jira, Notion, and Slack via MCP. Copy the prompt content and use it in a web conversation with the appropriate MCP integrations enabled.

## Customization

### Adding an Agent

Create `agents/my-agent.md`:

```yaml
---
name: my-agent
description: Brief description for when Claude should use this agent
model: opus
---

## Instructions

Your detailed agent instructions here...
```

### Adding a Command

Create `commands/my-command.md`. The filename becomes `/my-command`.

### Adding a Template

Create `settings-templates/my-stack.json`:

```json
{
  "_source": "my-stack",
  "_version": 1,
  "permissions": {
    "allow": [
      "Bash(my-cli-tool:*)",
      "WebFetch(domain:docs.my-tool.com)"
    ]
  }
}
```

Then use: `setup-project.sh my-stack`

## Keeping Settings in Sync

Check if your project settings match the templates:

```bash
cd ~/my-project
~/Development/claude-code-config/scripts/setup-project.sh --check django
```

Regenerate if drifted:

```bash
~/Development/claude-code-config/scripts/setup-project.sh django
```

## Git Setup for Projects

Add to your project's `.gitignore`:

```gitignore
# Claude Code symlinks (personal config)
.claude/agents
.claude/commands
.claude/skills
.claude/settings.json
```

**Do commit** `settings.local.json` if you want to share permissions with your team. The `settings.json` symlink is personal (plugin preferences), while `settings.local.json` contains project-specific permissions worth sharing.

## Uninstalling / Cleanup

**Remove global symlinks:**
```bash
rm ~/.claude/agents ~/.claude/commands ~/.claude/skills ~/.claude/settings.json
```

**Remove from a project:**
```bash
rm -rf .claude/agents .claude/commands .claude/skills .claude/settings.json
# Optionally remove generated permissions too:
rm .claude/settings.local.json
```

**Moving the repo to a new location:**
```bash
# After moving, re-run setup scripts to update symlinks
~/new-location/claude-code-config/scripts/setup-global.sh
cd ~/my-project && ~/new-location/claude-code-config/scripts/setup-project.sh django
```

## Troubleshooting

**Python not found**
```bash
python3 --version  # Need 3.8+
# macOS: brew install python@3.11
# Ubuntu: sudo apt install python3
```

**Symlinks broken after moving repo**
```bash
# Re-run both setups
~/claude-code-config/scripts/setup-global.sh
cd ~/my-project && ~/Development/claude-code-config/scripts/setup-project.sh django
```

**"Circular symlink" error**
You're running setup-project.sh from inside the config repo. Run it from your actual project directory instead.

## Requirements

- Bash shell (macOS, Linux, or WSL on Windows)
- Python 3.8+
- [Claude Code CLI](https://claude.ai/code)

### Windows Users

These scripts require a Unix-like environment. Options:
- **WSL (recommended)**: Install [Windows Subsystem for Linux](https://docs.microsoft.com/en-us/windows/wsl/install), then run scripts from within WSL
- **Git Bash**: May work but is not tested

Note: Symlinks created in WSL are not visible from native Windows applications.

## License

MIT - see [LICENSE](LICENSE)

## Contributing

PRs welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.
