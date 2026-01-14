# Claude Code Config

A collection of reusable agents, commands, and permission templates for [Claude Code](https://claude.ai/code).

## Features

- **9 specialized agents** for debugging, code review, testing, refactoring, and more
- **7 slash commands** for common workflows (commit, PR, review, standup)
- **7 composable permission templates** for Python, Django, React, Node.js, Go, and Terraform
- **Setup scripts** for easy configuration on new machines and projects

## Installation

```bash
# Clone the repository
git clone https://github.com/edjchapman/claude-code-config.git
cd claude-code-config

# Set up global config (creates symlinks in ~/.claude/)
./scripts/setup-global.sh
```

## Per-Project Setup

In any project directory:

```bash
# Python project
/path/to/claude-code-config/scripts/setup-project.sh python

# Django project
/path/to/claude-code-config/scripts/setup-project.sh django

# React frontend
/path/to/claude-code-config/scripts/setup-project.sh react

# Full-stack (Django + React)
/path/to/claude-code-config/scripts/setup-project.sh django react

# See all options
/path/to/claude-code-config/scripts/setup-project.sh --help
```

This creates in your project:
```
.claude/
├── agents   -> (symlink to repo agents)
├── commands -> (symlink to repo commands)
└── settings.local.json (merged from base + your templates)
```

## Directory Structure

```
claude-code-config/
├── agents/               # Custom agent definitions
├── commands/             # Custom slash commands
├── settings-templates/   # Permission templates by project type
│   ├── base.json         # Git, GitHub CLI, file operations
│   ├── python.json       # pytest, mypy, ruff, pip, uv, poetry
│   ├── django.json       # Django management, docker compose
│   ├── react.json        # npm, vitest, playwright
│   ├── node.json         # npm, yarn, pnpm, eslint
│   ├── go.json           # go build/test, golangci-lint
│   └── terraform.json    # terraform commands
├── scripts/
│   ├── setup-global.sh   # Configure ~/.claude/
│   ├── setup-project.sh  # Configure project .claude/
│   └── merge-settings.py # Merge templates
└── web_shortcuts/        # Web workflow shortcuts
```

## Available Agents

| Agent | Purpose | Model |
|-------|---------|-------|
| `bug-resolver` | Systematic debugging and root cause analysis | opus |
| `code-reviewer` | General code review for any language | opus |
| `django-code-reviewer` | Django-specific security/performance review | opus |
| `e2e-playwright-engineer` | Playwright E2E test creation | opus |
| `git-helper` | Complex git operations and recovery | sonnet |
| `pr-review-bundler` | Bundle PR reviews into markdown | opus |
| `refactoring-engineer` | Systematic code refactoring | opus |
| `spec-writer` | Technical specifications and planning | opus |
| `test-engineer` | Backend and frontend test creation | sonnet |

### Model Selection

- **Opus**: Complex analysis, security reviews, architectural decisions, planning
- **Sonnet**: Pattern-based tasks, test generation, git operations (faster, lower cost)

## Available Commands

| Command | Description |
|---------|-------------|
| `/standup` | Summarize last 24h of activity for standup |
| `/commit` | Analyze staged changes, generate commit message |
| `/pr` | Create PR with auto-generated description |
| `/review` | Review current changes before committing |
| `/explain` | Explain code at a specific location |
| `/lint` | Run all project linters |
| `/format-release-notes` | Format GitHub release notes |

## Available Templates

| Template | Permissions |
|----------|-------------|
| `base` | Git, GitHub CLI, find, mkdir, rm, WebSearch (always included) |
| `python` | pytest, mypy, ruff, black, pip, uv, poetry |
| `django` | Django management, docker compose, make |
| `react` | npm, npx, vitest, playwright, TypeScript |
| `node` | npm, yarn, pnpm, vitest, jest, eslint, prettier |
| `go` | go build/test/run, golangci-lint, staticcheck |
| `terraform` | terraform fmt/validate/plan/init |

## Customization

### Adding a New Agent

Create `agents/my-agent.md`:

```yaml
---
name: my-agent
description: When to use this agent
model: opus  # or sonnet
---

Your agent instructions here...
```

### Adding a New Command

Create `commands/my-command.md`. The filename becomes the command name (`/my-command`).

### Adding a New Template

Create `settings-templates/my-template.json`:

```json
{
  "_source": "my-template",
  "_version": 1,
  "permissions": {
    "allow": [
      "Bash(my-command:*)",
      "WebFetch(domain:docs.example.com)"
    ]
  }
}
```

Then use it: `setup-project.sh my-template`

## Troubleshooting

### Python not found

Setup scripts require Python 3.8+:

```bash
python3 --version
# macOS: brew install python@3.11
```

### Symlinks broken after moving repo

Re-run setup:

```bash
./scripts/setup-global.sh
# Then in each project:
/path/to/repo/scripts/setup-project.sh <types>
```

### Settings drift

Check and regenerate:

```bash
./scripts/setup-project.sh --check django
./scripts/setup-project.sh django  # regenerate
```

## What Stays Local

These are machine-specific and not symlinked:

- `~/.claude/settings.json` (MCP servers, API tokens)
- `~/.claude/settings.local.json` (machine-specific permissions)
- `~/.claude/history.jsonl`
- `~/.claude/projects/`

## Git Recommendations

For projects using this setup, add to `.gitignore`:

```gitignore
# Claude Code symlinks (point to personal config)
.claude/agents
.claude/commands
```

Keep `settings.local.json` tracked to share project permissions with your team.

## Requirements

- Python 3.8+
- Bash shell
- [Claude Code CLI](https://claude.ai/code)

## License

MIT License - see [LICENSE](LICENSE)

## Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.