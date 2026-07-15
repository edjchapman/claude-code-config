# Shared Activity Gathering

Common data-gathering steps for the activity-report skills (`/standup` and `/eow-review`). The calling SKILL.md defines the period (`$START_DATE` / `$END_DATE`), the output template, and any extra steps — this file defines how to collect the data.

## Step G1: Setup - Get User Identity

> This step must complete before Steps G2-G5. Steps G2-G5 can run in parallel.

**Git Identity:**

```bash
git config user.email && git config user.name
```

**Jira Identity:**
Use `mcp__plugin_atlassian_atlassian__atlassianUserInfo` to get the current user's account ID and display name.

Store these identities for filtering activity in subsequent steps.

## Step G2: Git Activity

> Note: Git commands only cover the current repository. If you work across multiple repos, mention this limitation and ask the user if they want to repeat for other repos.

```bash
# All commits by the user for the period
git log --author="$(git config user.email)" --since="$START_DATE" --until="$END_DATE" --format="%h %ai %s" --all --no-merges

# Commit count summary
git log --author="$(git config user.email)" --since="$START_DATE" --until="$END_DATE" --oneline --all --no-merges | wc -l
```

- Group commits by Jira ticket / feature branch and identify the main themes of work
- Note any refactoring, bug fixes, features, docs, or test work

## Step G3: GitHub PRs

```bash
# All PRs by the user (updated in the period)
gh pr list --author="@me" --state=all --limit=20 --json number,title,state,createdAt,mergedAt,updatedAt,url,reviews,additions,deletions --search "updated:>=$(date -v-${DAYS_AGO}d +%Y-%m-%d)"

# Currently open PRs
gh pr list --author="@me" --state=open --json number,title,url,createdAt,baseRefName,headRefName

# PRs reviewed by the user
gh pr list --search "reviewed-by:@me updated:>=$(date -v-${DAYS_AGO}d +%Y-%m-%d)" --state=all --limit=20 --json number,title,state,url
```

Replace `${DAYS_AGO}` with the number of days between today and `$START_DATE`. On macOS, use `date -v-Nd +%Y-%m-%d`; on Linux, use `date -d "N days ago" +%Y-%m-%d`.

- List PRs merged in the period with reviewer info
- Note PRs still open/awaiting review, and any closed without merging
- List PRs reviewed by the user (code reviews given)

## Step G4: Jira Activity (skip if `--skip-jira`)

**If Jira MCP is available (`mcp__plugin_atlassian_atlassian__*` tools):**

Use `mcp__plugin_atlassian_atlassian__searchJiraIssuesUsingJql` with:

```
JQL: assignee = currentUser() AND updated >= "$START_DATE" ORDER BY updated DESC
Fields: summary, status, issuetype, priority, updated, created, resolution, self
```

Use `$START_DATE` in `YYYY-MM-DD` format. Do NOT hardcode a relative offset like `-7d`.

For each ticket, extract:

- Current status and any status transitions in the period
- Issue type (Story, Bug, Task), priority, story points and sprint if available
- Whether it was resolved/done in the period
- Related PR numbers (from commit messages or branch names)
- The Jira base URL from the `self` field (e.g., `https://yourorg.atlassian.net`) for linking tickets

For project board context, read the board URL from the project's `CLAUDE.md` (look for a `## Jira` section with a `Board URL`). If absent, skip the board reference.

**If Jira MCP is NOT available:**
Ask the user:

> "I don't have direct Jira access. Please paste your Jira activity summary, or tell me:
>
> 1. Which tickets did you work on? (e.g., BIL-123, BIL-456)
> 2. What's the status of each?
> 3. Any blockers?"

## Step G5: Calendar / Meetings (skip if `--skip-calendar`)

**If Google Calendar MCP is available (`mcp__claude_ai_Google_Calendar__*` tools):**

1. Use `mcp__claude_ai_Google_Calendar__list_events` for `$START_DATE` through `$END_DATE`
2. Note meetings attended, recurring themes (planning, reviews, 1:1s), and any meetings that produced decisions or action items

**If Google Calendar MCP is NOT available:**
Ask the user about meetings attended in the period and any key outcomes or action items — ask rather than skip silently.

## Error Handling

If any source fails (MCP server unavailable, API error, empty results):

- **Continue** with the remaining sources - do not abort the entire report
- Note the unavailable source in the output (e.g., "Jira data unavailable - MCP server not connected")
- Ask the user if they want to manually provide data for the missing source

## Delivery

1. Parse `--output <path>` if provided, otherwise use the calling skill's default path
2. Write the document to the file using the Write tool and confirm the saved path to the user

> Scheduled cloud runs deliver differently: the routine posts the report as a
> comment on the pinned tracking issue (see CLAUDE.md's Automation section),
> since cloud sessions can't write local files.

## Shared Guidelines

- Focus on outcomes and progress, not just "worked on X"
- Group work by ticket/feature, not by source
- Flag blockers and open items prominently
- Link ticket references using the Jira base URL discovered from the API `self` field (e.g., `[PROJ-123](https://yourorg.atlassian.net/browse/PROJ-123)`) or the project `CLAUDE.md` `## Jira` section. If no base URL is available, include the bare ticket ID.
