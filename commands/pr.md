Help me create a pull request with a well-crafted description.

## Arguments

`$ARGUMENTS`

- `--draft` or `-d`: Create as draft PR
- `--base <branch>`: Specify base branch (default: main)
- Examples: `/pr --draft`, `/pr --base develop`

## Steps

1. **Understand current state**:
   ```bash
   git branch --show-current
   git log origin/main..HEAD --oneline
   git diff origin/main..HEAD --stat
   ```

2. **Analyze all commits** being included:
   - Read each commit message
   - Look at the actual changes with `git diff origin/main..HEAD`
   - Identify the main themes and purpose

3. **Check for related context**:
   - Look for ticket/issue numbers in branch name or commits
   - Check if there are related specs in `specs/` directory
   - Note any breaking changes or migrations

4. **Generate PR description** with this structure:
   ```markdown
   ## Summary
   <1-3 bullet points explaining what this PR does and why>

   ## Changes
   <Grouped list of significant changes>

   ## Testing
   <How this was tested or how reviewers should test>

   ## Notes for Reviewers
   <Any context that helps review: focus areas, known issues, follow-ups>
   ```

5. **Ask for confirmation** before creating:
   - Show the proposed title and description
   - Confirm the base branch (usually main)
   - Ask if ready to create

6. **Create the PR** (only when confirmed):
   ```bash
   gh pr create --title "<title>" --body "<body>"
   ```

## Output
Present the PR title and description for review, then create when approved.
Return the PR URL when complete.