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
- **Setup scripts** that work on any machine

## Quick Start

```bash
# 1. Clone (or fork if you want to customize)
git clone https://github.com/edjchapman/claude-code-config.git ~/claude-code-config

# 2. Set up global config
~/claude-code-config/scripts/setup-global.sh

# 3. Set up a project (from your project directory)
cd ~/my-django-project
~/claude-code-config/scripts/setup-project.sh django

# 4. Start using Claude Code - agents and commands are now available
claude
```

**Tip:** Add an alias for easier use:
```bash
# Add to ~/.bashrc or ~/.zshrc
alias claude-setup='~/claude-code-config/scripts/setup-project.sh'

# Then use it like:
claude-setup django react
```

## What Gets Created

**Global setup** (`setup-global.sh`) creates symlinks in `~/.claude/`:
```
~/.claude/
├── agents   -> ~/claude-code-config/agents
└── commands -> ~/claude-code-config/commands
```

**Project setup** (`setup-project.sh`) creates in your project:
```
your-project/.claude/
├── agents              -> ~/claude-code-config/agents
├── commands            -> ~/claude-code-config/commands
└── settings.local.json    (generated from templates)
```

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
~/claude-code-config/scripts/setup-project.sh python          # Python project
~/claude-code-config/scripts/setup-project.sh django          # Django
~/claude-code-config/scripts/setup-project.sh django react    # Full-stack
~/claude-code-config/scripts/setup-project.sh go              # Go project
~/claude-code-config/scripts/setup-project.sh node            # Node.js
~/claude-code-config/scripts/setup-project.sh terraform       # Infrastructure
~/claude-code-config/scripts/setup-project.sh all             # ALL templates
```

| Template | What It Allows |
|----------|----------------|
| `all` | All templates below combined |
| `base` | Git, GitHub CLI, file operations, WebSearch *(always included)* |
| `python` | pytest, mypy, ruff, black, isort, flake8, pylint, bandit, pre-commit, pip, uv, poetry |
| `django` | Django manage.py commands, docker compose, make, uv run (pytest, flake8, basedpyright) |
| `react` | npm, yarn, pnpm, vitest, playwright, TypeScript, eslint, prettier |
| `node` | npm, yarn, pnpm, vitest, jest, mocha, eslint, prettier, tsc, bun |
| `go` | go build/test/run, golangci-lint, staticcheck, dlv, mockgen, wire |
| `terraform` | terraform fmt/validate/plan/init |

## Available Agents

Invoke with `@agent-name` in Claude Code:

| Agent | What It Does | Model |
|-------|--------------|-------|
| `@bug-resolver` | Systematic debugging, root cause analysis | opus |
| `@code-reviewer` | General code review for any language | opus |
| `@django-code-reviewer` | Django security/performance review, N+1 detection | opus |
| `@e2e-playwright-engineer` | Create and debug Playwright E2E tests | opus |
| `@git-helper` | Complex git: rebase, conflicts, recovery | sonnet |
| `@pr-review-bundler` | Bundle PR reviews into markdown | opus |
| `@refactoring-engineer` | Systematic, safe refactoring | opus |
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
| `/format-release-notes` | Format GitHub release notes |

## Directory Structure

```
claude-code-config/
├── agents/                  # Agent definitions (markdown)
├── commands/                # Slash commands (markdown)
├── settings-templates/      # Permission templates (JSON)
├── scripts/
│   ├── setup-global.sh      # One-time machine setup
│   ├── setup-project.sh     # Per-project setup
│   └── merge-settings.py    # Template merger
└── web_shortcuts/           # Web workflow prompts (for claude.ai web interface)
```

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
~/claude-code-config/scripts/setup-project.sh --check django
```

Regenerate if drifted:

```bash
~/claude-code-config/scripts/setup-project.sh django
```

## Git Setup for Projects

Add to your project's `.gitignore`:

```gitignore
# Claude Code symlinks (personal config)
.claude/agents
.claude/commands
```

**Do commit** `settings.local.json` if you want to share permissions with your team.

## Uninstalling / Cleanup

**Remove global symlinks:**
```bash
rm ~/.claude/agents ~/.claude/commands
```

**Remove from a project:**
```bash
rm -rf .claude/agents .claude/commands
# Optionally remove settings too:
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
cd ~/my-project && ~/claude-code-config/scripts/setup-project.sh django
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
