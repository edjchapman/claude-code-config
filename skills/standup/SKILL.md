---
description: Prepare a standup document summarizing recent work activity across Git, GitHub, and Jira.
argument-hint: "[<period>] [--output <path>] [--team] [--skip-jira|--skip-calendar]"
---

Prepare a standup document summarizing my recent work activity.

## Arguments

`$ARGUMENTS`

- **Period**: Specify the look-back period (default: 24 hours)
  - Examples: `/standup 48 hours`, `/standup since Monday`, `/standup 3 days`
- **Output**: `--output <path>` - Save to custom file path
  - Default: `./standups/YYYY-MM-DD-standup.md`
- **Team**: `--team` - Include team activity overview (opt-in)
- **Skip sources**: `--skip-jira`, `--skip-calendar`

## Step 1: Setup - Get User Identity

**Jira Identity:**
Use `atlassianUserInfo` tool to get the current user's account ID and display name.

Store this identity for filtering activity in subsequent steps.

## Step 1.5: Read Daily Log

Check for today's daily log file at `./standups/YYYY-MM-DD-log.md` (where YYYY-MM-DD is today's date).

**If the file exists**, read it and extract:

1. **Status Updates** (`## Status Updates` section): These are the user's own words about their work. Treat these as high-priority context — prefer the user's phrasing when summarizing completed work and blockers.
2. **Session Summaries** (`## Session Summaries` section): These are auto-logged git commits from session-end hooks. Use these to supplement git log data — they may overlap with Step 2's git output, so de-duplicate by commit hash.

Store the extracted data to enrich later steps:

- Entries mentioning "blocked", "waiting", or "stuck" should surface as blockers
- Timestamps help establish the narrative flow of the day

**If the file does not exist**, proceed normally — the remaining steps will gather data from primary sources.

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

3. For project board context, read the board URL from the project's `CLAUDE.md` (look for a `## Jira` section with a `Board URL`). If absent, skip the board reference.
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

## Step 4: Calendar / Meetings (skip if `--skip-calendar`)

**If Google Calendar MCP is available (`mcp__claude_ai_Google_Calendar__*` tools):**

1. Use `mcp__claude_ai_Google_Calendar__list_events` for the specified period
2. Note meetings attended and any that suggest outcomes or action items worth reporting

**If Google Calendar MCP is NOT available:**
Ask the user:

> "I don't have calendar access. Any meetings you attended in the period? Key outcomes or action items?"

## Step 5: Team Activity (only if `--team` flag is provided)

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

## Step 6: Generate Output

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

**Calendar/Meetings** (if available):

- [Meeting name] - [outcome or action items]

---

### Team Activity (if --team flag used)

| Team Member | Recent Activity                    |
| ----------- | ---------------------------------- |
| [Name 1]    | BIL-XXX: [brief], BIL-YYY: [brief] |
| [Name 2]    | BIL-ZZZ: [brief]                   |
```

## Step 7: Save to File

1. Parse `--output <path>` if provided, otherwise use default
2. Create the `./standups/` directory if it doesn't exist:

   ```bash
   mkdir -p ./standups
   ```

3. Generate filename: `YYYY-MM-DD-standup.md` (e.g., `2025-01-15-standup.md`)
4. Write the standup document to the file using the Write tool
5. Confirm to user: "Standup saved to `./standups/YYYY-MM-DD-standup.md`"

> Scheduled cloud runs deliver differently: the daily routine posts the standup
> as a comment on the pinned tracking issue (see CLAUDE.md's Automation
> section), since cloud sessions can't write local files.

## Guidelines

- Keep the main standup section brief (1-2 min verbal delivery)
- Put detailed context in the "Activity Details" section
- Focus on outcomes and progress, not just "worked on X"
- Flag blockers prominently
- If asked about "today" plans but none are clear from In Progress tickets, ask the user what they're planning
- Link ticket references using the Jira base URL from the project's `CLAUDE.md` `## Jira` section, or via the `self` field returned by Atlassian MCP. If no base URL is configured, include the bare ticket ID (e.g., `TICKET-ID`).
- For team activity, keep summaries concise - one line per team member
