Prepare a standup document summarizing my recent work activity.

## Arguments

`$ARGUMENTS`

- Specify the look-back period (default: 24 hours)
- Examples: `/standup 48 hours`, `/standup since Monday`, `/standup 3 days`

## Step 1: Git Activity

```bash
# Get commits for the specified period
git log --since="24 hours ago" --author="$(git config user.name)" --oneline

# For each commit, get the full context
git show <hash> --stat
```

- Analyze commit messages and changes
- Group related commits by feature/ticket
- Note any PRs merged or created

## Step 2: Jira Activity

**If Jira MCP is available:**
- Search for issues assigned to me updated in the period
- Get ticket transitions (e.g., In Progress → Review)
- Get any comments I added

**If Jira MCP is NOT available:**
Ask the user:
> "I don't have direct Jira access. Please paste your Jira activity summary, or tell me:
> 1. Which tickets did you work on? (e.g., PROJ-123, PROJ-456)
> 2. What's the status of each?
> 3. Any blockers?"

## Step 3: Notion Activity

**If Notion MCP is available:**
- Search for pages I edited in the period
- Look for meeting notes, documentation updates

**If Notion MCP is NOT available:**
Ask the user:
> "I don't have direct Notion access. Did you update any documentation or meeting notes? If so, briefly describe what."

## Output Format

Generate a structured standup document:

```markdown
# Standup - [DATE]

## Yesterday / Since Last Standup
- [Completed item with ticket ref if applicable]
- [Another completed item]

## Today
- [Planned work item]
- [Another planned item]

## Blockers / Discussion Points
- [Any blockers or items needing team input]

---
### Activity Details

**Git Commits**: N commits across M files
- [Key changes summary]

**Tickets Updated**: [PROJ-123, PROJ-456]
- PROJ-123: [Brief status]
- PROJ-456: [Brief status]

**Documentation**: [Any Notion/docs updates]
```

## Guidelines
- Keep the main standup section brief (1-2 min verbal delivery)
- Put detailed context in the "Activity Details" section
- Focus on outcomes and progress, not just "worked on X"
- Flag blockers prominently
- If asked about "today" plans, ask the user what they're planning