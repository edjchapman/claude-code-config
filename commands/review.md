Review my current changes before I commit them.

## Arguments

`$ARGUMENTS`

- If a file path is provided, focus the review on that file
- If empty, review all staged and unstaged changes
- `--fix-suggestions`: Include exact code snippets for suggested fixes
- `--strict`: Flag more issues (style, naming, minor optimizations)
- Examples: `/review`, `/review src/auth.py`, `/review --fix-suggestions`

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

For each issue, provide:
- **Location**: `file:line`
- **Problem**: Brief description
- **Impact**: Why this matters
- **Fix** (if `--fix-suggestions` or obvious fix exists):
```python
# Before
problematic_code()

# After
fixed_code()
```

### Should Fix
[List important issues with same format as Critical]

### Suggestions
[List nice-to-haves]

If `--fix-suggestions` is provided, include code snippets for suggestions too.

### Files Reviewed
| File | Status | Issues |
|------|--------|--------|
| `path/to/file.py` | PASS / NEEDS WORK | 0 critical, 2 suggestions |

### Quick Fixes Available
If any issues have obvious automated fixes, list them:
- `file:line` - [description] - Can be auto-fixed with `command`

Keep feedback actionable and specific with file:line references.

## Integration with GitHub

**If GitHub MCP is available (`mcp__plugin_github_github__*`) and changes are for a PR:**
- Suggest creating a draft PR for early feedback
- Reference related issues if ticket ID found in branch name
