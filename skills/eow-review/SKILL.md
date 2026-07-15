---
name: eow-review
description: Prepare end-of-week review notes summarizing the full week's work activity across all sources (Git, GitHub, Jira).
argument-hint: "[<period>] [--output <path>] [--skip-jira|--skip-calendar|--skip-github]"
---

Prepare end-of-week review notes summarizing the full week's work activity across all sources.

**First, read `GATHERING.md` in the sibling `standup` skill directory** (`../standup/GATHERING.md` relative to this SKILL.md) — it defines the shared data-gathering steps (identity, git, GitHub PRs, Jira, calendar, error handling, delivery). This file defines only what is week-review-specific.

## Arguments

`$ARGUMENTS`

1. Extract `--output <path>` if present (default: `./eow-review-YYYY-MM-DD.md`)
2. Extract `--skip-jira`, `--skip-calendar`, `--skip-github` flags if present
3. Remaining text is the **period** specification (default: **7 days** / current week Mon-Fri)

**Compute `$START_DATE` and `$END_DATE`** from the period:

- No period given → `$START_DATE` = 7 days ago, `$END_DATE` = today
- `since Monday` → `$START_DATE` = most recent Monday, `$END_DATE` = today
- `2 weeks` → `$START_DATE` = 14 days ago, `$END_DATE` = today
- Explicit dates → use as provided

Use them consistently in **all** gathering steps.

Examples: `/eow-review`, `/eow-review since Monday`, `/eow-review 2 weeks`, `/eow-review --skip-calendar`

## Output Template

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

## Week-Review Guidelines

- The "Completed This Week" section should tell a narrative - what was the focus, what was delivered
- The "Other Work" section captures valuable work not tied to tickets (reviews, refactoring, tooling)
- Group calendar data by day for a daily schedule overview
- Include the "Next Week" section with planned work inferred from open tickets and upcoming calendar
- Keep the summary concise enough to present verbally in 2-3 minutes
