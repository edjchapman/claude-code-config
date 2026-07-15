---
name: git-workflow
description: Use when working with Git repositories, branches, commits, pull requests, release workflows, or files under .git — including complex operations like interactive rebase, merge-conflict resolution, cherry-picking, bisecting, or recovering lost commits via reflog.
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

## Complex Operations

Approach: understand the current state (`git status`, `git log`), assess what could be lost, create a safety net, then execute step by step.

### Safety Net Before Dangerous Operations

- Create a backup branch: `git branch backup-before-<operation>`
- Note current HEAD: `git rev-parse HEAD`
- Stash uncommitted changes: `git stash`
- If it goes wrong: `git rebase --abort` / `git merge --abort` / `git cherry-pick --abort`, or `git reset --hard <backup>`

### Recovering Lost Commits

```bash
git reflog                     # all recent HEAD positions - your safety net
git branch recovery <hash>     # create branch at a lost commit
git cherry-pick <hash>         # apply a lost commit to current branch
git checkout <commit> -- <file>  # restore one file from a commit
```

### Bisecting a Regression

```bash
git bisect start
git bisect bad HEAD
git bisect good <known-good>
git bisect run <test-command>  # exits 0 for good, non-zero for bad
git bisect reset               # when done
```

### Resolving Merge Conflicts

Resolve `<<<<<<<` markers per file, `git add` each, then `git rebase --continue` / `git merge --continue`. Keep one side wholesale with `git checkout --ours <file>` or `--theirs <file>`.

### Red Flags — Proceed with Caution

- `--force` push (prefer `--force-with-lease`), `reset --hard`
- Rebasing already-pushed commits
- Operating on shared branches (main, develop)
