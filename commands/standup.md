Prepare a standup document summarizing my recent work activity.

## Arguments

`$ARGUMENTS`

- **Period**: Specify the look-back period (default: 24 hours)
  - Examples: `/standup 48 hours`, `/standup since Monday`, `/standup 3 days`
- **Output**: `--output <path>` - Save to custom file path
  - Default: `./standups/YYYY-MM-DD-standup.md`
- **Team**: `--team` - Include team activity overview (opt-in)
- **Skip sources**: `--skip-jira`, `--skip-notion`, `--skip-slack`

## Step 1: Setup - Get User Identity

**Jira Identity:**
Use `atlassianUserInfo` tool to get the current user's account ID and display name.

**Notion Identity:**
Use `notion-get-users` tool to identify the current user.

Store these identities for filtering activity in subsequent steps.

## Step 2: Git Activity

```bash
# Get commits for the specified period
git log --since="24 hours ago" --author="$(git config user.name)" --oneline

# For each commit, get the full context
git show <hash> --stat

# Check for PRs created/merged
gh pr list --author=@me --state=all --limit=10
```

- Analyze commit messages and changes
- Group related commits by feature/ticket
- Note any PRs merged, created, or in review

## Step 3: Jira Activity

**If Jira MCP is available (`mcp__plugin_atlassian_atlassian__*` tools):**

Use the following tools:

- `mcp__plugin_atlassian_atlassian__atlassianUserInfo` - Get current user identity
- `mcp__plugin_atlassian_atlassian__searchJiraIssuesUsingJql` - Search for issues
- `mcp__plugin_atlassian_atlassian__getJiraIssue` - Get issue details

1. Get user's account ID from Step 1
2. Search for issues assigned to me updated in the period:

   ```
   JQL: assignee = '<accountId>' AND updated >= '-24h' ORDER BY updated DESC
   ```

3. For the project board context, reference: `https://builtai.atlassian.net/jira/software/projects/BIL/boards/42`
4. Extract from each ticket:
   - Status transitions (e.g., In Progress → Review)
   - Comments added/received
   - Story points if available
   - Sprint association

**If Jira MCP is NOT available:**
Ask the user:
> "I don't have direct Jira access. Please paste your Jira activity summary, or tell me:
>
> 1. Which tickets did you work on? (e.g., BIL-123, BIL-456)
> 2. What's the status of each?
> 3. Any blockers?"

## Step 4: Notion Activity

**If Notion MCP is available (`mcp__plugin_Notion_notion__*` tools):**

Use the following tools:

- `mcp__plugin_Notion_notion__notion-search` - Search for pages
- `mcp__plugin_Notion_notion__notion-get-users` - Get user information
- `mcp__plugin_Notion_notion__notion-create-pages` - Create new pages

1. Use `mcp__plugin_Notion_notion__notion-search` to find pages edited by current user
2. Filter results by `last_edited_time` within the specified period
3. Categorize by type:
   - Meeting notes
   - Documentation updates
   - Task databases
   - Other pages

**If Notion MCP is NOT available:**
Ask the user:
> "I don't have direct Notion access. Did you update any documentation or meeting notes? If so, briefly describe what."

## Step 5: Slack & Google Calendar via Notion AI Search

**Try Notion AI Search first:**
Use `mcp__plugin_Notion_notion__notion-search` with `content_search_mode="ai_search"` to search connected Slack and Google Drive sources:

- Query: "meetings discussions updates" for the specified period
- This may surface Slack threads and calendar events indexed by Notion

**Fallback prompt if no results or unavailable:**
Ask the user:
> "I couldn't find Slack/Calendar data through Notion. Please share:
>
> 1. Any important Slack discussions or decisions from the period?
> 2. Any meetings you attended? Key outcomes or action items?"

## Step 6: Team Activity (only if `--team` flag is provided)

**If `--team` flag is provided AND Jira MCP is available:**

1. Query for team activity (excluding current user):

   ```
   JQL: project = BIL AND updated >= '-24h' AND assignee != '<accountId>' ORDER BY assignee, updated DESC
   ```

2. Group results by assignee
3. Summarize each team member's activity:
   - Tickets moved/updated
   - Key status changes
   - Blockers flagged

**If `--team` flag is NOT provided:**
Skip this step entirely.

## Step 7: Generate Output

Create the standup document with all gathered information:

```markdown
# Standup - [DATE]

## Yesterday / Since Last Standup
- [Completed items with ticket refs, e.g., "Implemented auth flow (BIL-123)"]
- [Documentation updates]
- [Meetings attended]

## Today
- [Planned work from In Progress tickets]
- [Scheduled meetings/discussions]
- [Goals for the day]

## Blockers / Discussion Points
- [Any blockers flagged in Jira]
- [Items needing team input or decisions]
- [Dependencies on others]

---
### Activity Details

**Git Commits**: N commits across M files
- [Repo 1]: X commits - [summary of changes]
- [Repo 2]: Y commits - [summary of changes]

**Pull Requests**:
- [#123 - Title - Status (merged/open/draft)]

**Jira Tickets**:
| Ticket | Title | Status | Points |
|--------|-------|--------|--------|
| BIL-123 | Implement feature X | In Review | 3 |
| BIL-456 | Fix bug Y | Done | 1 |

**Notion/Documentation**:
- [Page name] - [type of update]

**Slack Highlights** (if available):
- [Key discussion or decision]

**Calendar/Meetings** (if available):
- [Meeting name] - [outcome or action items]

---
### Team Activity (if --team flag used)

| Team Member | Recent Activity |
|-------------|-----------------|
| [Name 1] | BIL-XXX: [brief], BIL-YYY: [brief] |
| [Name 2] | BIL-ZZZ: [brief] |
```

## Step 8: Save to File

1. Parse `--output <path>` if provided, otherwise use default
2. Create the `./standups/` directory if it doesn't exist:

   ```bash
   mkdir -p ./standups
   ```

3. Generate filename: `YYYY-MM-DD-standup.md` (e.g., `2025-01-15-standup.md`)
4. Write the standup document to the file using the Write tool
5. Confirm to user: "Standup saved to `./standups/YYYY-MM-DD-standup.md`"

**Optional Notion save:**
After saving locally, ask the user:
> "Would you like me to also save this standup to Notion?"

If yes, use `mcp__plugin_Notion_notion__notion-create-pages` to create a new page in their workspace.

## Guidelines

- Keep the main standup section brief (1-2 min verbal delivery)
- Put detailed context in the "Activity Details" section
- Focus on outcomes and progress, not just "worked on X"
- Flag blockers prominently
- If asked about "today" plans but none are clear from In Progress tickets, ask the user what they're planning
- Link ticket references when possible (e.g., `[BIL-123](https://builtai.atlassian.net/browse/BIL-123)`)
- For team activity, keep summaries concise - one line per team member
