---
description: Prepare end-of-week review notes summarizing the full week's work activity across all sources (Git, GitHub, Jira).
---

Prepare end-of-week review notes summarizing the full week's work activity across all sources.

## Arguments

`$ARGUMENTS`

Parse the arguments as follows:

1. Extract `--output <path>` if present (default: `./eow-review-YYYY-MM-DD.md`)
2. Extract `--skip-jira`, `--skip-calendar`, `--skip-github` flags if present
3. Remaining text is the **period** specification (default: `7 days` / current week Mon-Fri)

**Compute `START_DATE` and `END_DATE`** from the period:

- No period given → `START_DATE` = 7 days ago, `END_DATE` = today
- `since Monday` → `START_DATE` = most recent Monday, `END_DATE` = today
- `2 weeks` → `START_DATE` = 14 days ago, `END_DATE` = today
- Explicit dates → use as provided

Use `START_DATE` and `END_DATE` consistently in **all** subsequent steps.

Examples: `/eow-review`, `/eow-review since Monday`, `/eow-review 2 weeks`, `/eow-review --skip-calendar`

## Step 1: Setup - Get User Identity

> This step must complete before Steps 2-5. Steps 2-5 can run in parallel.

**Git Identity:**

```bash
git config user.email && git config user.name
```

**Jira Identity:**
Use `mcp__plugin_atlassian_atlassian__atlassianUserInfo` tool to get the current user's account ID and display name.

Store these identities for filtering activity in subsequent steps.

## Step 2: Git Activity

> Note: Git commands only cover the current repository. If you work across multiple repos, mention this limitation and ask the user if they want to repeat for other repos.

Run these commands to understand the week's work:

```bash
# Get all commits by the user for the period
git log --author="$(git config user.email)" --since="$START_DATE" --until="$END_DATE" --format="%h %ai %s" --all --no-merges

# Get commit count summary
git log --author="$(git config user.email)" --since="$START_DATE" --until="$END_DATE" --oneline --all --no-merges | wc -l
```

- Group commits by Jira ticket / feature branch
- Identify the main themes of work
- Note any refactoring, bug fixes, features, docs, or test work

## Step 3: GitHub PRs

```bash
# Get all PRs by the user (updated in the period)
gh pr list --author="@me" --state=all --limit=20 --json number,title,state,createdAt,mergedAt,updatedAt,url,reviews,additions,deletions --search "updated:>=$(date -v-${DAYS_AGO}d +%Y-%m-%d)"

# Get currently open PRs
gh pr list --author="@me" --state=open --json number,title,url,createdAt,baseRefName,headRefName

# Get PRs reviewed by the user
gh pr list --search "reviewed-by:@me updated:>=$(date -v-${DAYS_AGO}d +%Y-%m-%d)" --state=all --limit=20 --json number,title,state,url
```

Replace `${DAYS_AGO}` with the number of days between today and `START_DATE`. On macOS, use `date -v-Nd +%Y-%m-%d`; on Linux, use `date -d "N days ago" +%Y-%m-%d`.

- List all PRs merged this period with reviewer info
- Note any PRs still open/awaiting review
- Note any PRs closed without merging (and why, if apparent from title)
- List PRs reviewed by the user (code reviews given)

## Step 4: Jira Activity

**If Jira MCP is available (`mcp__plugin_atlassian_atlassian__*` tools):**

Use `mcp__plugin_atlassian_atlassian__searchJiraIssuesUsingJql` with:

```
JQL: assignee = currentUser() AND updated >= "$START_DATE" ORDER BY updated DESC
Fields: summary, status, issuetype, priority, updated, created, resolution, self
```

Use `$START_DATE` in `YYYY-MM-DD` format (e.g., `2026-01-23`). Do NOT hardcode `-7d`.

For each ticket, extract:

- Current status and any status transitions this period
- Issue type (Story, Bug, Task)
- Priority level
- Whether it was resolved/done this period
- Related PR numbers (from commit messages or branch names)
- The Jira base URL from the `self` field (e.g., extract `https://yourorg.atlassian.net` from the API response) for linking tickets

**If Jira MCP is NOT available:**
Ask the user to provide their ticket activity.

## Step 5: Calendar / Meetings (skip if `--skip-calendar`)

**If Google Calendar MCP is available (`mcp__claude_ai_Google_Calendar__*` tools):**

1. Use `mcp__claude_ai_Google_Calendar__list_events` for `$START_DATE` through `$END_DATE`
2. Group meetings by day for a daily schedule overview
3. Note recurring themes (planning, reviews, 1:1s) and any meetings that produced decisions or action items

**If Google Calendar MCP is NOT available:**
Ask the user about meetings and documentation updates.

## Error Handling

If any source fails (MCP server unavailable, API error, empty results):

- **Continue** with the remaining sources - do not abort the entire review
- Note the unavailable source in the output (e.g., "Jira data unavailable - MCP server not connected")
- Ask the user if they want to manually provide data for the missing source

## Step 6: Generate Output

Create the end-of-week review document with all gathered information. Use this structure:

```markdown
# End of Week Review - DD Month YYYY

**Author:** [Name]
**Week:** DD Mon - DD Mon YYYY

---

## Summary

[2-3 sentence high-level summary of the week's primary focus areas and key deliverables]

---

## Completed This Week

### [Ticket ID]: [Title] ([Type], [Priority])

**Status:** [Current Status]

[Bullet points describing work done, PRs merged, key decisions made]

[Repeat for each ticket worked on, ordered by importance/effort]

---

## Other Work

- [Ad-hoc commits not linked to any ticket]
- [Code reviews given (PRs reviewed for others)]
- [Non-ticket work: refactoring, tooling, documentation]

---

## Git Activity

- **N commits** this week across all branches
- **N PRs merged**, N currently open
- **N PRs reviewed** for others
- Primary reviewers: [names]

## Pull Requests

| #    | Title   | Status      | Merged | Reviewers | +/-   |
| ---- | ------- | ----------- | ------ | --------- | ----- |
| NNNN | [Title] | Merged/Open | DD Mon | [names]   | +N/-N |

## Jira Tickets

| Key       | Summary   | Type           | Status           |
| --------- | --------- | -------------- | ---------------- |
| PROJ-NNNN | [Summary] | Story/Bug/Task | Done/In Progress |

## Meetings & Calendar

| Date | Meeting    |
| ---- | ---------- |
| Mon  | [meetings] |
| Tue  | [meetings] |
| Wed  | [meetings] |
| Thu  | [meetings] |
| Fri  | [meetings] |

## Blockers / Risks

- [Any open blockers, PRs awaiting review, unresolved issues]

## Next Week

- [Planned work, follow-ups, upcoming priorities]
```

## Step 7: Save to File

1. Parse `--output <path>` if provided, otherwise use default
2. Generate filename: `eow-review-YYYY-MM-DD.md` (e.g., `eow-review-2026-01-30.md`)
3. Write the document to the file using the Write tool
4. Confirm to user: "EOW review saved to `./eow-review-YYYY-MM-DD.md`"

## Guidelines

- Step 1 (identity) must complete before Steps 2-5. Steps 2-5 can run in parallel.
- Focus on outcomes and deliverables, not just activity
- Group work by ticket/feature, not by source
- The "Completed This Week" section should tell a narrative - what was the focus, what was delivered
- The "Other Work" section captures valuable work not tied to tickets (reviews, refactoring, tooling)
- Flag blockers and open items prominently
- Link ticket references using the Jira base URL discovered from the API `self` field (e.g., `[PROJ-123](https://yourorg.atlassian.net/browse/PROJ-123)`)
- Include the "Next Week" section with planned work inferred from open tickets and upcoming calendar
- Keep the summary concise enough to present verbally in 2-3 minutes
- Calendar data comes from the Google Calendar MCP connector; if it is not connected, ask rather than skip silently
- Scheduled cloud runs deliver as a comment on the pinned tracking issue (see CLAUDE.md's Automation section) instead of a local file
