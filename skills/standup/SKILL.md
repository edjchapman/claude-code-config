---
name: standup
description: Prepare a standup document summarizing recent work activity across Git, GitHub, and Jira.
argument-hint: "[<period>] [--output <path>] [--team] [--skip-jira|--skip-calendar]"
---

Prepare a standup document summarizing my recent work activity.

**First, read [`GATHERING.md`](GATHERING.md) in this skill's directory** — it defines the shared data-gathering steps (identity, git, GitHub PRs, Jira, calendar, error handling, delivery). This file defines only what is standup-specific.

## Arguments

`$ARGUMENTS`

- **Period**: look-back period (default: **24 hours**). Examples: `/standup 48 hours`, `/standup since Monday`, `/standup 3 days`
- **Output**: `--output <path>` (default: `./standups/YYYY-MM-DD-standup.md`)
- **Team**: `--team` - Include team activity overview (opt-in)
- **Skip sources**: `--skip-jira`, `--skip-calendar`

Compute `$START_DATE` / `$END_DATE` from the period and use them in all gathering steps.

## Standup-Specific Step: Read Daily Log

Before the shared gathering steps, check for today's daily log at `./standups/YYYY-MM-DD-log.md`.

**If it exists**, extract:

1. **Status Updates** (`## Status Updates` section): the user's own words about their work. Treat as high-priority context — prefer the user's phrasing when summarizing completed work and blockers.
2. **Session Summaries** (`## Session Summaries` section): auto-logged git commits from session-end hooks. De-duplicate against git log output by commit hash.

Entries mentioning "blocked", "waiting", or "stuck" should surface as blockers. If the file does not exist, proceed normally.

## Standup-Specific Step: Team Activity (only if `--team`)

If `--team` is provided AND Jira MCP is available, query team activity (excluding the current user):

```
JQL: project = BIL AND updated >= '-24h' AND assignee != '<accountId>' ORDER BY assignee, updated DESC
```

Group results by assignee; summarize each member's tickets moved, key status changes, and blockers flagged — one line per team member.

## Output Template

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

**Pull Requests**:

- [#123 - Title - Status (merged/open/draft)]

**Jira Tickets**:
| Ticket | Title | Status | Points |
|--------|-------|--------|--------|
| BIL-123 | Implement feature X | In Review | 3 |

**Calendar/Meetings** (if available):

- [Meeting name] - [outcome or action items]

---

### Team Activity (if --team flag used)

| Team Member | Recent Activity                    |
| ----------- | ---------------------------------- |
| [Name 1]    | BIL-XXX: [brief], BIL-YYY: [brief] |
```

## Standup Guidelines

- Keep the main standup section brief (1-2 min verbal delivery); detailed context goes in "Activity Details"
- If asked about "today" plans but none are clear from In Progress tickets, ask the user what they're planning
- Save to `./standups/` (create the directory with `mkdir -p ./standups` if needed)
