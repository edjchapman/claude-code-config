---
name: git-workflow
description: Enforces conventional commits, branch naming conventions, and PR size guidelines.
globs:
  - ".git/**"
---

# Git Workflow

Follow these conventions for all git operations in this project.

## Commit Messages

Use [Conventional Commits](https://www.conventionalcommits.org/) format:

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

### Types
- `feat`: New feature or functionality
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Formatting, missing semicolons (no code change)
- `refactor`: Code restructuring (no feature/fix)
- `test`: Adding or updating tests
- `chore`: Maintenance tasks, dependencies
- `ci`: CI/CD changes
- `perf`: Performance improvements

### Rules
- First line under 72 characters
- Imperative mood: "add feature" not "added feature"
- No period at end of subject line
- Blank line between subject and body
- Reference issue/ticket in footer: `Refs: PROJ-123`

## Branch Naming

```
<type>/<ticket>-<short-description>
```

Examples:
- `feature/BIL-123-user-authentication`
- `fix/BIL-456-login-redirect-loop`
- `chore/BIL-789-upgrade-dependencies`

## Pull Request Guidelines

### Size
- Aim for under 400 lines changed
- If larger, split into stacked PRs or feature flags
- One logical change per PR

### Description
- Summary of what and why (not how)
- Link to ticket/issue
- Test plan: how to verify the change
- Screenshots for UI changes

### Review Checklist
- Tests pass
- No linting errors
- No TODO/FIXME without linked tickets
- Migration safety considered (for DB changes)
- Backwards compatibility assessed
