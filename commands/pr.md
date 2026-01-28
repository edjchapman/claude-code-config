Help me create a pull request with a well-crafted description.

## Arguments

`$ARGUMENTS`

- `--draft` or `-d`: Create as draft PR
- `--base <branch>`: Specify base branch (default: main)
- `--notion`: Save PR details to Notion after creation
- Examples: `/pr --draft`, `/pr --base develop`, `/pr --notion`

## Jira Configuration

- **Base URL**: `https://builtai.atlassian.net/browse/`
- **Ticket Patterns**: `BIL-XXXX`, `ABC-123`, `#123`, `GH-123`

## Steps

### Step 1: Understand current state

```bash
git branch --show-current
git log origin/main..HEAD --oneline
git diff origin/main..HEAD --stat
```

### Step 2: Analyze all commits being included

- Read each commit message
- Look at the actual changes with `git diff origin/main..HEAD`
- Identify the main themes and purpose

### Step 3: Check for related context

- Look for ticket/issue numbers in branch name or commits
- Check if there are related specs in `specs/` directory
- Note any breaking changes or migrations

### Step 4: Extract Jira context from branch name

Extract ticket ID from branch name patterns:

- `feature/BIL-123-description` → `BIL-123`
- `fix/BIL-456-bug-fix` → `BIL-456`
- `BIL-789/some-feature` → `BIL-789`

**If Jira MCP is available (`mcp__plugin_atlassian_atlassian__getJiraIssue`):**

- Fetch ticket summary, description, acceptance criteria
- Extract linked issues and epic context
- Auto-populate "Related Issues" section in PR with ticket details

**If Jira MCP is NOT available but ticket ID found:**

- Add Jira link to PR body: `Related: [BIL-123](https://builtai.atlassian.net/browse/BIL-123)`
- Note: "Jira details not available - add acceptance criteria manually if needed"

### Step 5: Check for PR template

Search for PR templates in order:

1. `.github/PULL_REQUEST_TEMPLATE.md`
2. `.github/PULL_REQUEST_TEMPLATE/default.md`
3. `.github/pull_request_template.md`
4. `docs/pull_request_template.md`

**If template found:**

- Use template as base structure for PR body
- Merge Jira context and commit analysis into template sections
- Fill in template placeholders where possible

**If no template found:**

- Use default structure (see Step 6)

### Step 6: Generate PR description

**Default structure (if no template):**

```markdown
## Summary
<1-3 bullet points explaining what this PR does and why>

## Changes
<Grouped list of significant changes>

## Testing
<How this was tested or how reviewers should test>

## Notes for Reviewers
<Any context that helps review: focus areas, known issues, follow-ups>

## Related Issues
- [BIL-XXX](https://builtai.atlassian.net/browse/BIL-XXX) - {summary from Jira if available}
```

### Step 7: Ask for confirmation before creating

- Show the proposed title and description
- Confirm the base branch (usually main)
- If Jira ticket found, confirm linking is correct
- Ask if ready to create

### Step 8: Create the PR (only when confirmed)

```bash
gh pr create --title "<title>" --body "<body>"
```

### Step 9: Save to Notion (if `--notion` flag)

**If Notion MCP is available (`mcp__plugin_Notion_notion__notion-create-pages`):**

- Create a new page with PR details:
  - **Title**: PR title
  - **Properties**: Status (Open), Created date, PR URL
  - **Content**: Summary, changes, testing notes, related Jira tickets
- Return the Notion page URL alongside PR URL

**If Notion MCP is NOT available:**

- Skip Notion save
- Inform user: "Notion MCP not available - PR created but not saved to Notion"

## Output

Present the PR title and description for review, then create when approved.
Return the PR URL when complete (and Notion URL if `--notion` used).
