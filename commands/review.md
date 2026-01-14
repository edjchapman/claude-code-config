Review my current changes before I commit them.

## Arguments

`$ARGUMENTS`

- If a file path is provided, focus the review on that file
- If empty, review all staged and unstaged changes

## Steps

1. **Check what's changed**:
   ```bash
   git status
   git diff          # unstaged changes
   git diff --cached # staged changes
   ```

2. **Analyze all modified files**:
   - Read the full diff for each file
   - Understand the context of changes

3. **Review for**:

   ### Critical Issues (must fix)
   - Security vulnerabilities
   - Obvious bugs or logic errors
   - Breaking changes without handling
   - Sensitive data exposure

   ### Important Issues (should fix)
   - Missing error handling
   - Performance concerns
   - Missing tests for new functionality
   - Incomplete implementations (TODOs, FIXMEs)

   ### Suggestions (nice to have)
   - Code style improvements
   - Better naming
   - Simplification opportunities
   - Documentation gaps

4. **Check for common mistakes**:
   - Console.log / print statements left in
   - Commented-out code
   - Debugging code
   - Hardcoded values that should be config
   - Missing type annotations

## Output Format

### Ready to Commit? [YES/NO/NEEDS WORK]

### Critical Issues
[List any blocking issues]

### Should Fix
[List important issues]

### Suggestions
[List nice-to-haves]

### Files Reviewed
[List of files with brief status]

Keep feedback actionable and specific with file:line references.