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

Example structure:
```yaml
---
name: my-agent
description: Brief description of when to use this agent
model: opus  # or sonnet for simpler tasks
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