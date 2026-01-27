Analyze my staged changes and help me write a good commit message.

## Arguments

`$ARGUMENTS`

- If provided, use as a hint for the commit message or scope
- `--no-ticket`: Skip Jira ticket extraction and linking
- Examples: `/commit auth changes`, `/commit fix typo`, `/commit --no-ticket`

## Jira Configuration

- **Base URL**: `https://builtai.atlassian.net/browse/` (customize per-project in CLAUDE.md)
- **Ticket Patterns**: `BIL-XXXX`, `ABC-123`

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

4. **Extract Jira ticket from branch name** (skip if `--no-ticket`):
   ```bash
   git branch --show-current
   ```

   Extract ticket ID from branch name patterns:
   - `feature/BIL-123-description` → `BIL-123`
   - `fix/BIL-456-bug-fix` → `BIL-456`
   - `BIL-789/some-feature` → `BIL-789`
   - Common patterns: `[A-Z]+-[0-9]+` (e.g., `ABC-123`, `PROJ-456`)

   **If Jira MCP is available (`mcp__plugin_atlassian_atlassian__getJiraIssue`):**
   - Fetch ticket summary to validate and provide context
   - Use ticket title to inform commit message scope

   **If Jira MCP is NOT available but ticket ID found:**
   - Include ticket reference in commit message
   - Note: "Jira details not available - using ticket ID only"

5. **Generate commit message** following conventional commits format:
   ```
   <type>(<scope>): <description>

   - bullet point explaining a change
   - another bullet point if needed

   Refs: BIL-123
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
   - **Ticket reference**: If ticket found and not `--no-ticket`, add on separate line:
     - Format: `Refs: BIL-123` or `Fixes: BIL-123` (for bug fixes)
     - Include Jira link if helpful: `Refs: BIL-123 (https://builtai.atlassian.net/browse/BIL-123)`

6. **Present options**:
   - Provide 2-3 commit message options if the changes are ambiguous
   - Ask if they want to proceed with the commit

## Output
Present the suggested commit message(s) and ask if the user wants to:
- Use one of the suggestions
- Modify a suggestion
- Provide their own message

Do NOT actually run `git commit` unless explicitly asked.