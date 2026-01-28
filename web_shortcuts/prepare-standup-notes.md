Help me prepare for my daily standup meeting this morning. Base it on my activity since yesterday morning.

## Instructions

Gather my recent activity from the following sources (skip any that are not configured):

1. **Git/GitHub**: Recent commits, PRs opened/merged, code reviews
2. **Jira/Linear**: Tickets I worked on, status changes, comments
3. **Slack**: Relevant team discussions (if accessible)
4. **Notion**: Any documentation I edited

## Configuration

Set these environment variables or provide URLs when prompted:

```
STANDUP_JIRA_URL=https://your-org.atlassian.net/jira/software/projects/XXX/boards/YY
STANDUP_NOTION_URL=https://www.notion.so/your-workspace-id
STANDUP_SLACK_URL=https://app.slack.com/client/TEAM_ID/CHANNEL_ID
STANDUP_GITHUB_URL=https://github.com/your-org/your-repo
```

## Output Format

Summarize my activity in this format:

**Yesterday:**

- [Completed tasks, PRs merged, bugs fixed]

**Today:**

- [Planned work based on in-progress tickets]

**Blockers:**

- [Any identified blockers or dependencies]

If Notion is configured, create a page in my private section for standups and meetings (if it doesn't exist) and save these notes there.
