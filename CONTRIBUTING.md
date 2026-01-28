# Contributing

Thanks for your interest in contributing to Claude Code Config!

## How to Contribute

### Development Setup

This repository uses pre-commit hooks to maintain code quality. Follow these steps to set up your development environment:

#### Prerequisites

- Python 3.8+
- Node.js (for markdownlint)
- Git

#### Installation

1. **Install pre-commit**:

   ```bash
   pip install pre-commit
   ```

2. **Install the git hooks**:

   ```bash
   pre-commit install
   ```

3. **Test your setup** (optional):

   ```bash
   pre-commit run --all-files
   ```

#### What Pre-commit Does

Pre-commit automatically runs these checks on every commit:

- **File hygiene**: Removes trailing whitespace, adds EOF newlines, normalizes line endings
- **Shell scripts**: Linting with `shellcheck`, formatting with `shfmt`
- **Python**: Formatting and linting with `ruff`
- **Markdown**: Style checking with `markdownlint`
- **JSON/YAML**: Syntax validation
- **Custom checks**: Duplicate name detection, frontmatter validation, settings merge tests

Typical commit time is 3-5 seconds. Most issues are auto-fixed.

#### Manual Quality Checks

If you prefer not to install pre-commit, you can run checks manually:

```bash
# Shell script linting
shellcheck scripts/*.sh scripts/hooks/*.sh

# Python formatting
pip install ruff
ruff format scripts/
ruff check scripts/ --fix

# JSON validation
python -m json.tool settings.json
for f in settings-templates/*.json; do python -m json.tool "$f"; done

# Test settings merging
python scripts/merge-settings.py settings-templates base django

# Validate frontmatter
pip install pyyaml
python scripts/validate-frontmatter.py agents name description model
python scripts/validate-frontmatter.py skills name description globs

# Check for duplicate names
bash scripts/hooks/check-duplicates.sh
```

#### CI Pipeline

All pull requests run the same checks via GitHub Actions. The CI workflow:

1. Runs all pre-commit hooks on all files
2. Runs fallback validation jobs (JSON, Markdown, shellcheck)

If pre-commit passes locally, CI should pass too.

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

All code style is enforced by pre-commit hooks:

- **Shell scripts**: Linted with `shellcheck`, formatted with `shfmt` (2-space indent)
- **Python**: Formatted and linted with `ruff` (100 char line length)
- **Markdown**: Linted with `markdownlint` (fenced code blocks, no line length limits)
- **JSON**: Validated with `python -m json.tool`

Style is automatically applied on commit. No manual formatting needed.

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
