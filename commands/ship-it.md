Run the full shipping workflow: verify quality, commit, push, and create a PR.

> **Purpose**: End-to-end quality gate that ensures tests pass, linters are clean, and changes are committed before creating a PR. Combines the verification steps you'd normally do manually into a single command.

## Arguments

`$ARGUMENTS`

- `--draft` or `-d`: Create PR as draft
- `--base <branch>`: Specify base branch (default: main)
- `--skip-tests`: Skip test verification (use sparingly)
- `--notion`: Save PR details to Notion after creation
- Examples: `/ship`, `/ship --draft`, `/ship --base develop`

## Steps

### Step 1: Pre-flight Checks

Verify the working state is shippable:

```bash
git status
git branch --show-current
git log origin/main..HEAD --oneline
```

- Confirm we're on a feature branch (not main)
- Check for uncommitted changes that need staging
- Verify there are commits to ship

### Step 2: Run Tests

```bash
# Detect test runner and run full suite
# Python: pytest, Django test, or manage.py test
# JS/TS: npm test, yarn test, or npx jest
```

- Run the project's test suite
- **If tests fail, STOP.** Report failures and do not proceed.
- If `--skip-tests` was passed, warn but continue

### Step 3: Run Linters

```bash
# Detect and run project linters
# Python: ruff check, ruff format --check
# JS/TS: eslint, prettier --check
```

- Run available linters
- If linter errors exist, attempt auto-fix and re-check
- Report any remaining issues

### Step 4: Stage and Commit

If there are uncommitted changes:

1. Show the diff and ask what to include
2. Stage the relevant files
3. Generate a commit message following conventional commits
4. Confirm the commit message with the user
5. Create the commit

If all changes are already committed, skip to Step 5.

### Step 5: Push

```bash
git push -u origin $(git branch --show-current)
```

- Push the branch to remote
- If push fails (e.g., behind remote), report and ask how to proceed

### Step 6: Create PR

Delegate to the `/pr` command workflow:

- Analyze all commits on the branch
- Generate PR title and description
- Check for Jira ticket in branch name
- If `--draft` was passed, create as draft
- If `--notion` was passed, save to Notion

Present the PR for confirmation before creating.

## Output

### Ship Report

```
Ship: [branch-name]
────────────────────────────────
Tests:   PASS (N passed)
Linter:  PASS
Commits: N commits
Push:    origin/[branch]
PR:      [URL]
────────────────────────────────
```

## Guidelines

- Never ship if tests are failing (unless `--skip-tests`)
- Always confirm the PR description before creating
- If the branch has merge conflicts with the base, report and stop
- Keep the workflow transparent — show each step's result before proceeding
