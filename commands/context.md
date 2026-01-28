Refresh context: show current branch, recent commits, open PRs, and project status.

## Arguments

`$ARGUMENTS`

- Optional flags:
  - `--full`: Include extended details (open issues, CI status)
  - `--branch`: Branch info only
- Example: `/context`, `/context --full`

## Steps

### 1. Git Status

```bash
git branch --show-current
git status --short
```

Show:
- Current branch name
- Uncommitted changes count (staged, unstaged, untracked)

### 2. Recent Commits

```bash
git log --oneline -10
```

Show the last 10 commits on the current branch.

### 3. Branch Comparison

```bash
git log --oneline main..HEAD 2>/dev/null || git log --oneline master..HEAD 2>/dev/null
```

Show:
- How many commits ahead of main/master
- Whether the branch is up-to-date with remote

### 4. Open Pull Requests (if gh CLI available)

```bash
gh pr list --author @me --state open --limit 5
```

Show the user's open PRs with their status.

### 5. CI Status (if --full and gh available)

```bash
gh run list --branch $(git branch --show-current) --limit 3
```

Show recent CI run results for the current branch.

### 6. Extended Info (if --full)

```bash
gh issue list --assignee @me --state open --limit 5
```

Show open issues assigned to the user.

## Output

Present a concise dashboard:

```
Context Refresh
===============
Branch:     feature/BIL-123-user-auth
Status:     3 modified, 1 untracked
Ahead of main: 4 commits

Recent commits:
  abc1234 feat(auth): add JWT refresh flow
  def5678 test(auth): add login endpoint tests
  ...

Open PRs:
  #142 feat: user authentication [REVIEW REQUESTED]
  #139 fix: password reset email [MERGED]
```
