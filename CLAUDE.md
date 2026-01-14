# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Purpose

This is a configuration repository for Claude Code. It provides reusable agents, commands, and permission templates that can be symlinked to `~/.claude/` (global) or `.claude/` (per-project) directories. Changes here propagate to all linked projects automatically.

## Key Scripts

```bash
# Global setup (creates ~/.claude/agents and ~/.claude/commands symlinks)
./scripts/setup-global.sh

# Project setup (run from target project directory)
~/claude-code-config/scripts/setup-project.sh <template> [template2...]
~/claude-code-config/scripts/setup-project.sh --list       # Show templates
~/claude-code-config/scripts/setup-project.sh --check django   # Check drift + symlinks
~/claude-code-config/scripts/setup-project.sh --status     # Show current config state
~/claude-code-config/scripts/setup-project.sh --dry-run django # Preview changes

# Merge templates (used internally by setup-project.sh)
python3 scripts/merge-settings.py <templates-dir> base <type1> [type2...]
```

## Architecture

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

### Agent Definitions

Agents in `agents/` are Markdown files with YAML frontmatter:
- `name`: Agent identifier (used as `@agent-name`)
- `description`: When Claude should invoke this agent (include examples)
- `model`: `opus` for complex reasoning, `sonnet` for pattern-based tasks

### Command Definitions

Commands in `commands/` are Markdown files where the filename becomes the slash command (e.g., `commit.md` → `/commit`).

## Code Style

- Shell scripts: Use `shellcheck` for linting
- Python: Format with `black`, lint with `ruff`
- JSON: Validate with `python -m json.tool`

## Commit Messages

Follow conventional commits:
```
feat(agents): add kubernetes-helper agent
fix(scripts): handle spaces in paths
docs: update template documentation
```