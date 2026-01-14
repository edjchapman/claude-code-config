Analyze my staged changes and help me write a good commit message.

## Arguments

`$ARGUMENTS`

- If provided, use as a hint for the commit message or scope
- Examples: `/commit auth changes`, `/commit fix typo`

## Steps

1. **Check staged changes**:
   ```bash
   git diff --cached --stat
   git diff --cached
   ```

2. **Analyze the changes**:
   - What files were modified?
   - What is the nature of the change? (feature, fix, refactor, docs, test, chore)
   - What is the scope/impact?

3. **Review recent commit style**:
   ```bash
   git log --oneline -10
   ```

4. **Check for ticket reference**:
   - Look at branch name for ticket pattern (e.g., `feature/ABC-123-description`)
   - Common patterns: `ABC-123`, `#123`, `GH-123`
   - If found, include in commit message

5. **Generate commit message** following conventional commits format:
   ```
   <type>(<scope>): <description>

   - bullet point explaining a change
   - another bullet point if needed

   Refs: ABC-123
   ```

   Types: feat, fix, docs, style, refactor, test, chore, ci, perf

   Guidelines:
   - First line: type(scope): description
   - Type should be lowercase
   - Scope is the area/module affected (e.g., auth, api, ui)
   - Description should be concise, imperative mood, no period
   - Keep first line under 72 characters
   - Blank line after the first line
   - Bullet points describe specific changes made
   - Ticket reference on separate line if found (Refs: ABC-123)

6. **Present options**:
   - Provide 2-3 commit message options if the changes are ambiguous
   - Ask if they want to proceed with the commit

## Output
Present the suggested commit message(s) and ask if the user wants to:
- Use one of the suggestions
- Modify a suggestion
- Provide their own message

Do NOT actually run `git commit` unless explicitly asked.