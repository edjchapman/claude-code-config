Guide me through creating a hotfix: branch from main, apply a minimal fix, run targeted tests, and prepare a PR.

## Arguments

`$ARGUMENTS`

- Describe the bug or issue that needs an urgent fix
- Example: `/hotfix users getting 500 on password reset`

## Steps

### 1. Create Hotfix Branch

```bash
git fetch origin main
git checkout -b hotfix/<short-description> origin/main
```

Ask the user to confirm the branch name before creating it.

### 2. Investigate the Issue

- Locate the relevant code based on the bug description
- Identify the root cause with minimal investigation
- Focus on the immediate fix, not broader refactoring

### 3. Apply Minimal Fix

- Make the **smallest possible change** that resolves the issue
- Do NOT refactor surrounding code
- Do NOT add features or improvements
- Add a targeted test that reproduces the bug and verifies the fix

### 4. Verify

Run only the tests directly related to the fix:

- Python: `pytest <specific_test_file> -x -v`
- TypeScript: `npx vitest run <specific_test_file>`
- Also run the full test suite if fast enough

### 5. Prepare PR

Use `gh pr create` with:

- Title: `hotfix: <description>`
- Label: `hotfix` (if available)
- Body should include:
  - **Problem**: What was broken
  - **Root Cause**: Why it happened
  - **Fix**: What was changed and why
  - **Risk**: Assessment of the fix's impact
  - **Test Plan**: How the fix was verified

### 6. Post-Fix Checklist

Present to the user:

- [ ] Fix is minimal and targeted
- [ ] Test reproduces the original bug
- [ ] Test passes with the fix
- [ ] No unrelated changes included
- [ ] PR description explains the urgency

## Output

Present the PR URL when complete and remind the user to:

- Request expedited review
- Monitor deployment after merge
- Consider if a follow-up ticket is needed for deeper investigation
