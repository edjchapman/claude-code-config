Prepare technical analysis for backlog refinement meetings.

## Arguments

`$ARGUMENTS`

- List of Jira ticket IDs: `/refinement BIL-3606 BIL-3580 BIL-3252`
- JQL query: `/refinement --jql "status='Ready to Refine'"`
- Output directory: `/refinement BIL-3606 --output ./refinement-2026-01-17/`
- Exploration depth: `/refinement BIL-3606 --explore thorough` (quick|medium|thorough)
- Save to Notion: `/refinement BIL-3606 --notion`

## Step 1: Fetch Tickets

**If Jira MCP is available (`mcp__plugin_atlassian_atlassian__*` tools):**

Use the following tools:

- `mcp__plugin_atlassian_atlassian__getJiraIssue` - Get issue details
- `mcp__plugin_atlassian_atlassian__searchJiraIssuesUsingJql` - Search with JQL

```
For each ticket ID:
  - mcp__plugin_atlassian_atlassian__getJiraIssue(issueIdOrKey="BIL-XXXX")
  - Extract: summary, description, priority, status, comments, story_points
```

**If Jira MCP is NOT available:**
> "I don't have direct Jira access. Please provide ticket details in one of these formats:
>
> 1. Jira REST API JSON (paste from `https://builtai.atlassian.net/rest/api/2/issue/BIL-XXXX`)
> 2. Copy/paste the ticket description from Jira
> 3. Tell me the ticket IDs and I'll ask for details on each"

## Step 2: Explore Codebase

For each ticket, launch an Explore agent to find relevant code:

```
Task(subagent_type="Explore", prompt="""
Find code related to: {ticket.summary}

Context from ticket:
{ticket.description}

Search for:
1. Related components, models, APIs
2. Similar existing implementations
3. Test files
4. Migration patterns (if data changes needed)

Return:
- Key files with line numbers
- Existing patterns to follow
- Potential complexity factors
""")
```

Run up to 3 Explore agents in parallel for efficiency.

## Step 3: Analyze & Estimate

For each ticket, determine:

**Story Points (Fibonacci: 1, 2, 3, 5, 8, 13):**

| Factor | 1-2 pts | 3-5 pts | 8-13 pts |
|--------|---------|---------|----------|
| Files touched | 1-2 | 3-5 | 6+ |
| Backend changes | None | Model or API | Model + API + Migration |
| Frontend changes | None | Single component | Multiple components |
| New patterns | Following existing | Minor adaptation | New architecture |
| Dependencies | None | 1-2 tickets | Blocked or complex chain |

**Generate for each ticket:**

1. Implementation steps (bullet points)
2. Key files to modify
3. Clarifying questions
4. Risk assessment

## Step 4: Generate Output

Create output directory structure:

```
{output_dir}/
├── README.md                     # Index with summary table
├── BIL-XXXX_{title_snake_case}.md  # Individual ticket files
└── ...
```

**Individual Ticket File Template:**

```markdown
# {ticket.key}: {ticket.summary}

**Story Points:** {estimated_points}
**Priority:** {ticket.priority}
**Status:** {ticket.status}

**Description:** {ticket.description | summarized}

---

## Key Files

| File | Purpose | Lines |
|------|---------|-------|
| `path/to/file.py` | Model changes | 50-75 |
| ... | ... | ... |

---

## Implementation Steps

1. Step one
2. Step two
3. ...

---

## Clarifying Questions

- Question 1?
- Question 2?

---

## Risk Assessment

**Risk Level:** Low | Medium | High

**Primary Risk:** Description

**Mitigation:** How to address
```

**Index File (README.md) Template:**

```markdown
# Backlog Refinement - {date}

## Summary Table

| Ticket | Title | Points | Complexity | Risk | Details |
|--------|-------|--------|------------|------|---------|
| BIL-XXXX | Title | **N** | Low/Med/High | Low/Med/High | [View](./BIL-XXXX_title.md) |

---

## Dependencies

{dependency_diagram}

---

## Action Items

- [ ] Action item from refinement
```

## Step 5: Present Summary

After generating files, present:

1. **Summary table** of all tickets with estimates
2. **Key risks** across all tickets
3. **Dependencies** between tickets
4. **Recommended discussion order** for refinement meeting

Ask:
> "I've created refinement documents in `{output_dir}/`. Would you like me to:
>
> 1. Add meeting notes after your refinement session?
> 2. Update story points in Jira? (requires Jira MCP)
> 3. Create any additional analysis?"

## Step 6: Save to Notion (if `--notion` flag)

**If Notion MCP is available (`mcp__plugin_Notion_notion__notion-create-pages`):**

- Create a new page for the refinement session:
  - **Title**: "Refinement - {date}"
  - **Content structure**:
    - Summary table (all tickets with estimates, complexity, risk)
    - Dependencies diagram
    - Individual ticket sections (collapsible if possible)
    - Action items checklist
  - **Properties**: Date, Sprint (if known), Total story points
- Return the Notion page URL

**If Notion MCP is NOT available:**

- Skip Notion save
- Inform user: "Notion MCP not available - files saved locally but not to Notion"

**Output with `--notion`:**
> "Refinement analysis complete:
>
> - Local files: `{output_dir}/`
> - Notion: {url}
>
> Total: {n} tickets, {total_points} story points estimated"

## Guidelines

- Default output directory: `./refinement/` in project root
- Use architecture patterns from CLAUDE.md when exploring (if available)
- Keep estimates conservative - round up when uncertain
- Flag blockers and dependencies prominently
- If ticket description is vague, generate more clarifying questions
- Cross-reference related tickets if they appear in the batch
