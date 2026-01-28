# Contributing

Thanks for your interest in contributing to Claude Code Config!

## How to Contribute

### Reporting Issues

- Check existing issues before creating a new one
- Include your OS, Python version, and Claude Code version
- Provide steps to reproduce the issue

### Adding Agents

1. Create a new file in `agents/` with `.md` extension
2. Include frontmatter with `name`, `description`, and `model`
3. Write clear, actionable instructions
4. Test the agent with Claude Code before submitting

#### Frontmatter Fields

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Agent identifier (used as `@agent-name`) |
| `description` | Yes | When Claude should use this agent (include examples) |
| `model` | Yes | `opus` for complex reasoning, `sonnet` for simpler tasks |
| `color` | No | UI accent color: `blue`, `orange`, `green`, `purple`, etc. |

Example structure:
```yaml
---
name: my-agent
description: Brief description of when to use this agent
model: opus  # or sonnet for simpler tasks
color: blue  # optional UI color
---

## Overview
What this agent does...

## First Steps
1. Step one
2. Step two

## Guidelines
- Guideline one
- Guideline two
```

### Adding Commands

1. Create a new file in `commands/` with `.md` extension
2. The filename (without `.md`) becomes the command name
3. Keep commands focused on a single task
4. Document any required arguments

#### Available Variables

Commands can use these special variables that Claude Code substitutes:

| Variable | Description |
|----------|-------------|
| `$ARGUMENTS` | Arguments passed after the command (e.g., `/commit fix typo` → `fix typo`) |

Example command structure:
```markdown
Analyze the staged changes and help write a commit message.

## Arguments

`$ARGUMENTS`

- If provided, use as a hint for the commit message
- If empty, analyze changes to determine the message

## Steps

1. Check staged changes with `git diff --cached`
2. Generate appropriate commit message
```

### Adding Templates

1. Create a new file in `settings-templates/` with `.json` extension
2. Follow the existing structure:
```json
{
  "_source": "template-name",
  "_version": 1,
  "permissions": {
    "allow": [...],
    "deny": [...]
  }
}
```
3. Only include permissions specific to your use case
4. Use specific patterns over broad wildcards when possible

### Adding Skills

Skills are domain knowledge documents that auto-activate based on file glob patterns.

1. Create a new file in `skills/` with `.md` extension
2. Include frontmatter with `name`, `description`, and `globs`
3. Write clear, actionable guidelines (not tutorials)
4. Focus on rules and patterns, not explanations

#### Frontmatter Fields

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Skill identifier |
| `description` | Yes | Brief description of what the skill covers |
| `globs` | Yes | Array of file glob patterns that activate this skill |

Example structure:
```yaml
---
name: my-skill
description: Brief description of the domain knowledge
globs:
  - "**/*.py"
  - "**/tests/**"
---

# My Skill

## Guidelines
- Guideline one
- Guideline two
```

### Adding Hooks

Hooks are shell scripts in `scripts/hooks/` referenced by `settings.json`.

1. Create a new script in `scripts/hooks/` with `.sh` extension
2. Make it executable: `chmod +x scripts/hooks/my-hook.sh`
3. Add the hook reference to `settings.json` under the appropriate event
4. Follow these conventions:
   - Exit 0 for success / allow
   - Exit 2 for block (PreToolUse hooks)
   - Check for required tools before using them (graceful degradation)
   - Only run on relevant file types
   - Keep execution fast (under 5 seconds)

### Code Style

- Shell scripts: Use `shellcheck` for linting
- Python: Use `black` for formatting, `ruff` for linting
- JSON: Validate with `python -m json.tool`

### Pull Request Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Make your changes
4. Test your changes locally
5. Commit with a clear message
6. Push and create a Pull Request

### Commit Messages

Follow conventional commits:
```
feat(agents): add kubernetes-helper agent
fix(scripts): handle spaces in paths
docs: update template documentation
```

## Questions?

Open an issue with the "question" label.