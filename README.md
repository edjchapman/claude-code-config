# Claude Code Config

[![Validate Config](https://github.com/edjchapman/claude-code-config/actions/workflows/validate-config.yml/badge.svg)](https://github.com/edjchapman/claude-code-config/actions/workflows/validate-config.yml)

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
- **Rules** for path-scoped code style enforcement
- **Setup scripts** that work on any machine

## Quality Standards

This repository maintains high code quality through automated checks:

- ✅ **Pre-commit hooks**: Auto-format code, lint, validate syntax (< 5s per commit)
- ✅ **CI validation**: GitHub Actions runs all checks on every PR
- ✅ **Shell scripts**: Linted with `shellcheck`, formatted with `shfmt`
- ✅ **Python**: Formatted and linted with `ruff`
- ✅ **Markdown**: Style checked with `markdownlint`
- ✅ **JSON/YAML**: Syntax validation
- ✅ **Custom checks**: Duplicate name detection, frontmatter validation, settings merge tests

See [CONTRIBUTING.md](CONTRIBUTING.md) for setup instructions.

## Quick Start

```bash
# 1. Clone (or fork if you want to customize)
git clone https://github.com/edjchapman/claude-code-config.git ~/claude-code-config

# 2. Set up global config
~/Development/claude-code-config/scripts/setup-global.sh

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
├── agents            -> ~/Development/claude-code-config/agents
├── commands          -> ~/Development/claude-code-config/commands
├── skills            -> ~/Development/claude-code-config/skills
├── rules             -> ~/Development/claude-code-config/rules
├── settings.json     -> ~/Development/claude-code-config/settings.json
└── keybindings.json  -> ~/Development/claude-code-config/keybindings.json
```

**Project setup** (`setup-project.sh`) creates in your project:

```
your-project/
├── .mcp.json (MCP server config, if applicable)
└── .claude/
    ├── agents              -> ~/Development/claude-code-config/agents
    ├── commands            -> ~/Development/claude-code-config/commands
    ├── skills              -> ~/Development/claude-code-config/skills
    ├── rules               -> ~/Development/claude-code-config/rules
    ├── settings.json       -> ~/Development/claude-code-config/settings.json
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
| `docker` | Docker build, compose, buildx, system commands |
| `java` | Gradle, Maven, Java compilation (javac, jar) |
| `kubernetes` | kubectl, helm, kustomize, kubectx, stern |
| `rust` | cargo, rustc, rustup, rustfmt, clippy |
| `terraform` | terraform fmt/validate/plan/init |

## Available Agents

### Orchestrator Agents

These coordinate multiple specialist agents to complete multi-phase workflows end-to-end:

| Agent | What It Does | Phases | Model |
|-------|--------------|--------|-------|
| `@implement` | Feature implementation: plan → code → test → review | spec-writer, test-engineer, code-reviewer | sonnet |
| `@fix` | Bug fix: investigate → fix → regression test → review | bug-resolver, test-engineer, code-reviewer | sonnet |
| `@review-pr` | PR review: context → code review → security → coverage | pr-review-bundler, code-reviewer, security-auditor, test-engineer | sonnet |
| `@refactor` | Safe refactoring: analyze → safety-net tests → refactor → review | refactoring-engineer, test-engineer, code-reviewer | sonnet |
| `@ship` | Pre-merge gate: assess → review → security → test → commit → PR | code-reviewer, security-auditor | sonnet |

### Specialist Agents

Invoke with `@agent-name` in Claude Code:

| Agent | What It Does | Model |
|-------|--------------|-------|
| `@bug-resolver` | Systematic debugging, root cause analysis | opus |
| `@career-adviser` | CV/resume review, LinkedIn optimization, interview prep | opus |
| `@ci-debugger` | CI/CD failure investigation, flaky tests | opus |
| `@code-reviewer` | General code review for any language | opus |
| `@content-reviewer` | Review promotional content: LinkedIn posts, PR announcements, conference talks, blog posts | sonnet |
| `@database-architect` | Schema design, migration planning, query optimization | opus |
| `@dependency-manager` | Dependency audit, outdated packages, license checks | sonnet |
| `@devops-engineer` | Infrastructure, CI/CD pipelines, containers | opus |
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
| `/eow-review` | Prepare end-of-week review notes |
| `/security-scan` | Run security audit on the codebase |

## CLI Scripts

Headless Claude Code scripts for automation. Add aliases to your shell profile for quick access:

```bash
alias cr='~/Development/claude-code-config/scripts/cli/review-changes.sh'
alias cpr='~/Development/claude-code-config/scripts/cli/review-pr.sh'
alias cdr='~/Development/claude-code-config/scripts/cli/daily-report.sh'
alias cee='~/Development/claude-code-config/scripts/cli/explain-error.sh'
```

| Script | Usage | What It Does |
|--------|-------|--------------|
| `review-changes.sh` | `cr` | Review uncommitted changes for bugs, security, code quality |
| `explain-error.sh` | `cmd 2>&1 \| cee` | Pipe error output to Claude for explanation |
| `daily-report.sh` | `cdr` | Summarize last 24h of git activity |
| `review-pr.sh` | `cpr 123` | Headless PR review |

### Git Pre-Push Hook (Optional)

Claude can review your diff before pushing (non-blocking):

```bash
git config core.hooksPath ~/Development/claude-code-config/githooks
```

## MCP Templates

MCP server configurations per project type, generated alongside `settings.local.json`:

| Template | MCP Servers |
|----------|-------------|
| `base` | None (MCP is opt-in) |
| `django` | PostgreSQL (`@modelcontextprotocol/server-postgres`) |
| `react` | Playwright (`@playwright/mcp`) |

MCP templates are automatically merged when running `setup-project.sh` if a matching template exists.

## GitHub Actions Templates

Copy these workflow files to your project's `.github/workflows/` directory:

| Template | Trigger | What It Does |
|----------|---------|--------------|
| `claude-pr-review.yml` | Pull request | Reviews PRs for bugs, security, test coverage |
| `claude-issue-triage.yml` | Issue opened | Labels, estimates complexity, suggests files |
| `claude-changelog.yml` | Release created | Generates grouped release notes |

```bash
# Copy a workflow to your project
cp ~/Development/claude-code-config/github-actions/claude-pr-review.yml .github/workflows/
# Set the ANTHROPIC_API_KEY secret in your repo settings
```

## macOS Automation

### LaunchAgent (Daily Report)

Auto-generate daily reports at 9am:

```bash
cp ~/Development/claude-code-config/macos/launchagents/com.claude.daily-report.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.claude.daily-report.plist
```

Reports are saved to `~/claude-reports/YYYY-MM-DD.md`.

### Raycast Script Commands

Copy scripts to your Raycast script commands directory:

```bash
cp ~/Development/claude-code-config/macos/raycast/*.sh ~/raycast-scripts/
```

## Directory Structure

```
claude-code-config/
├── agents/                  # Agent definitions (markdown)
├── commands/                # Slash commands (markdown)
├── skills/                  # Auto-activating domain knowledge (markdown)
├── rules/                   # Path-scoped code style rules (markdown)
├── settings-templates/      # Permission templates (JSON)
├── mcp-templates/           # MCP server templates (JSON)
├── settings.json            # Plugin config + hooks (symlinked globally)
├── keybindings.json         # Custom keybindings (symlinked globally)
├── templates/               # Example files (CLAUDE.local.md.example)
├── scripts/
│   ├── setup-global.sh      # One-time machine setup
│   ├── setup-project.sh     # Per-project setup
│   ├── merge-settings.py    # Permission template merger
│   ├── merge-mcp.py         # MCP template merger
│   ├── hooks/               # Hook scripts referenced by settings.json
│   │   ├── session-context.sh
│   │   ├── statusline.sh
│   │   ├── project-init.sh
│   │   ├── session-end.sh
│   │   ├── format-python.sh
│   │   ├── format-js.sh
│   │   ├── dangerous-cmd-check.sh
│   │   ├── check-duplicates.sh
│   │   ├── format-on-edit.sh
│   │   ├── pre-compact-state.sh
│   │   ├── notify-permission.sh
│   │   └── log-tool-failure.sh
│   └── cli/                 # Headless CLI automation scripts
│       ├── review-changes.sh
│       ├── explain-error.sh
│       ├── daily-report.sh
│       └── review-pr.sh
├── githooks/                # Optional git hooks
│   └── pre-push
├── github-actions/          # GitHub Actions workflow templates
│   ├── claude-pr-review.yml
│   ├── claude-issue-triage.yml
│   └── claude-changelog.yml
├── macos/                   # macOS automation
│   ├── launchagents/
│   │   └── com.claude.daily-report.plist
│   └── raycast/
│       ├── claude-review-changes.sh
│       └── claude-open-project.sh
└── web_shortcuts/           # Web workflow prompts (for claude.ai web interface)
```

## Hooks

Hooks are configured in `settings.json` and run automatically at key points in the Claude Code lifecycle. Since `settings.json` is symlinked globally, hooks work in all projects.

| Hook | Trigger | What It Does |
|------|---------|--------------|
| SessionStart | New session | Outputs git branch, recent commits, and dirty files |
| Setup (init) | Project init | Detects project type, suggests configuration |
| UserPromptSubmit | Before prompt sent | LLM checks if prompt is specific enough to act on |
| PostToolUse (Write/Edit) | After file edits | Auto-formats Python (ruff) and JS/TS (prettier) |
| PostToolUseFailure | After tool failure | Logs failure details to `~/.claude/debug/tool-failures.log` |
| PreToolUse (Bash) | Before commands | Blocks dangerous patterns (`rm -rf /`, `dd`, etc.) |
| Stop | Session end | LLM checks: tests run? linters run? TODOs left? |
| SubagentStop | Before subagent returns | LLM checks if subagent completed its task fully |
| PreCompact | Before compaction | Saves working state (branch, staged files, recent commits) |
| Notification | Permission needed | Sends macOS desktop notification (with tool details) |
| SessionEnd | Session ends | Logs session info, cleans up temp files |

Hook scripts live in `scripts/hooks/` and only run when the required tools are available (e.g., `ruff`, `prettier`).

## Skills

Skills are domain knowledge documents that auto-activate when you touch matching files. They provide passive guidance without explicit invocation.

| Skill | Activates On | What It Covers |
|-------|-------------|----------------|
| `git-workflow` | `.git/**` | Conventional commits, branch naming, PR size |
| `testing-patterns` | `test_*.py`, `*_test.py`, `*.test.ts`, `*.spec.ts`, etc. | AAA pattern, factories, coverage |
| `security-review` | `auth/**`, `middleware/**`, `security/**`, `routes/**` | Input validation, JWT, CSRF, secrets |
| `api-design` | `views/**`, `api/**`, `routes/**`, `controllers/**`, `endpoints/**` | REST conventions, status codes, pagination |
| `django-patterns` | `models.py`, `views.py`, `managers.py`, `signals.py`, etc. | Fat models, managers, query optimization, signals |
| `docker-patterns` | `Dockerfile`, `docker-compose*.yml`, `.dockerignore` | Multi-stage builds, layer caching, security |
| `infrastructure` | `*.tf`, `k8s/**/*.yaml`, `helm/**` | Terraform modules, K8s resources, Helm charts |

## Rules

Rules are path-scoped code style enforcement files in `rules/`. They use `paths` frontmatter for granular file matching and are enforced when touching matching files.

| Rule | Applies To | What It Enforces |
|------|-----------|-----------------|
| `python-style` | `**/*.py` | Naming, error handling, imports, type hints |
| `typescript-style` | `**/*.ts`, `**/*.tsx` | Naming, error handling, type usage |
| `react-style` | `**/*.tsx` | Component structure, props, hooks, state |

Rules were extracted from the former `coding-standards` skill. Skills provide domain knowledge (patterns and best practices), while rules enforce style requirements.

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
.claude/rules
.claude/settings.json
```

**Do commit** `settings.local.json` if you want to share permissions with your team. The `settings.json` symlink is personal (plugin preferences), while `settings.local.json` contains project-specific permissions worth sharing.

## Uninstalling / Cleanup

**Remove global symlinks:**

```bash
rm ~/.claude/agents ~/.claude/commands ~/.claude/skills ~/.claude/rules ~/.claude/settings.json
```

**Remove from a project:**

```bash
rm -rf .claude/agents .claude/commands .claude/skills .claude/rules .claude/settings.json
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
~/Development/claude-code-config/scripts/setup-global.sh
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
