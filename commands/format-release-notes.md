# Format Release Notes

Format GitHub release notes for Jira and stakeholder communication.

## Arguments

`$ARGUMENTS`

**Options:**

- `--fetch <tag>`: Fetch release notes for a specific tag (e.g., `--fetch v103`)
- `--no-fetch`: Disable auto-fetch; prompt for pasted input instead
- `--no-slack`: Skip Slack mrkdwn file generation
- `--no-notion`: Skip Notion database entry
- `--no-publish`: Skip GitHub release body update
- `--local-only`: Shorthand for `--no-slack --no-notion --no-publish` (only save local files)

**Positional:**

- `format`: `both` (default), `md`, or `csv`
- `version`: Override auto-detected version (e.g., `v103`)

**Examples:**

- `/format-release-notes` - Fetch latest, generate all outputs (md, csv, Slack, Notion, GitHub)
- `/format-release-notes --fetch v103` - Fetch specific tag, all outputs
- `/format-release-notes --no-fetch md` - Paste notes manually, md only
- `/format-release-notes --local-only` - Only save local files (md + csv), skip Slack/Notion/publish
- `/format-release-notes --no-publish` - All outputs except GitHub release update

## Instructions

### Step 1: Resolve Project Configuration

Resolve project-specific values dynamically instead of using hardcoded defaults.

**GitHub repo:**

```bash
gh repo view --json nameWithOwner -q '.nameWithOwner'
```

**Jira base URL:**

- Check `CLAUDE.md` for a Jira URL override (look for `atlassian.net` or a `jira_base_url` key)
- Fall back to `https://builtai.atlassian.net/browse/`

**Ticket pattern:**

- Auto-detect from PR titles using `[A-Z]+-[0-9]+`
- Common patterns: `BIL-1234`, `ABC-123`, `PROJ-456`

Store these resolved values for use in formatting steps:

- `REPO` — e.g., `Built-AI/clarion_app`
- `JIRA_BASE_URL` — e.g., `https://builtai.atlassian.net/browse/`
- `TICKET_PATTERN` — regex for ticket IDs found in PR titles

### Step 2: Determine Input Source

**Default (no flags):** Fetch the latest release automatically:

```bash
# Get latest release tag
gh release list --limit 1 --json tagName -q '.[0].tagName'
# Then fetch that release
gh release view <tag> --json body,tagName,name -q '{body: .body, tag: .tagName, name: .name}'
```

**If `--fetch <tag>` provided:** Fetch the specified release:

```bash
gh release view <tag> --json body,tagName,name -q '{body: .body, tag: .tagName, name: .name}'
```

**If `--no-fetch` provided:**
Prompt the user to paste their raw release notes.

### Step 3: Parse and Categorize

1. **Parse** the release notes (from GitHub fetch or user-provided input)
2. **Extract version** from the release title or tag
3. **Categorize** each PR into sections

### Categories

Order sections by importance to stakeholders:

| Category | Include |
|----------|---------|
| **Breaking Changes** | API changes, removed endpoints, migration required |
| **New Features** | New functionality (group by domain area dynamically) |
| **Improvements** | Enhancements to existing features |
| **Bug Fixes** | Defect corrections |
| **Security** | Security patches, dependency CVE fixes |
| **Deprecations** | Features marked for removal |
| **Maintenance** | Chores, refactoring, test improvements, dependency bumps |
| **New Contributors** | First-time contributors with their debut PR link |

Omit empty sections from output.

### Formatting Rules

- Link tickets: `[BIL-1234]({JIRA_BASE_URL}BIL-1234)` (using resolved Jira URL)
- Link PRs: `[#123](https://github.com/{REPO}/pull/123)` (using resolved repo)
- **One PR per line** — never group multiple PRs on the same line
- Same ticket can appear on multiple lines if it has multiple PRs
- Include contributors: `@username`
- Strip conventional commit prefixes (`feat:`, `fix:`, `chore:`)
- PRs without ticket IDs: List under their category without a ticket link
- Dependabot PRs: List individually under Maintenance > Dependency Updates with bump description
- Revert PRs: Note as "(reverted)" on the original PR line if both present
- Separate sections with `---` horizontal rules
- End with `**Full Changelog**: <GitHub compare URL>`

### Step 4: Format Outputs

Generate all output formats (unless individually opted out with `--no-*` flags or `--local-only`). Each format targets a different audience: markdown has full detail for developers, CSV has structured data for tracking, and Slack has an executive summary for stakeholders.

#### Markdown (`release-notes-{version}.md`)

```markdown
# Release Candidate {version}

## Summary

- **X new features** across {dynamically detected domain areas}
- **X bug fixes**
- **X improvements**
- **X maintenance items** (including X dependency updates)

---

## Breaking Changes

- [{TICKET}]({JIRA_BASE_URL}{TICKET}) Description [#456](https://github.com/{REPO}/pull/456) @dev

---

## New Features

### {Domain Area}

- [{TICKET}]({JIRA_BASE_URL}{TICKET}) Description [#123](https://github.com/{REPO}/pull/123) @contributor

---

## Improvements

- [{TICKET}]({JIRA_BASE_URL}{TICKET}) Description [#125](https://github.com/{REPO}/pull/125) @contributor

---

## Bug Fixes

- [{TICKET}]({JIRA_BASE_URL}{TICKET}) Description [#126](https://github.com/{REPO}/pull/126) @contributor

---

## Maintenance

### Code Quality

- [{TICKET}]({JIRA_BASE_URL}{TICKET}) Description [#127](https://github.com/{REPO}/pull/127) @contributor

### Dependency Updates

- [#130](https://github.com/{REPO}/pull/130) Bump package-name X.X to Y.Y @dependabot
- [#131](https://github.com/{REPO}/pull/131) Bump package-name X.X to Y.Y @dependabot

---

## New Contributors

- @username made their first contribution in [#132](https://github.com/{REPO}/pull/132)

---

**Full Changelog**: https://github.com/{REPO}/compare/prev-tag...current-tag
```

#### CSV (`release-notes-{version}.csv`)

```
Release,Category,Subcategory,Ticket,Ticket Link,Description,Contributors,PR Number,PR Link
{version},New Features,{Domain},{TICKET},{JIRA_BASE_URL}{TICKET},Description,@contributor,123,https://github.com/{REPO}/pull/123
{version},Bug Fixes,,{TICKET},{JIRA_BASE_URL}{TICKET},Description,@contributor,126,https://github.com/{REPO}/pull/126
{version},Maintenance,Dependency Updates,,,Bump package-name X.X to Y.Y,@dependabot,130,https://github.com/{REPO}/pull/130
{version},New Contributors,,,,"@username made their first contribution",@username,132,https://github.com/{REPO}/pull/132
```

**CSV notes:**

- One row per PR (same ticket can appear on multiple rows if it has multiple PRs)
- Leave cells empty for optional fields (Subcategory, Ticket, Ticket Link) when not applicable
- Dependency updates use `@dependabot` as contributor

#### Slack mrkdwn (`release-notes-{version}.slack.txt`) — unless `--no-slack` or `--local-only`

Write a file using Slack `mrkdwn` syntax (not standard Markdown). Key differences:

- Bold: `*text*` (not `**text**`)
- Links: `<url|text>` (not `[text](url)`)
- No heading syntax — use bold + emoji for section headers

Structure:

```
:rocket: *Release {version}*

*{X}* new features · *{Y}* bug fixes · *{Z}* improvements · *{W}* maintenance

:sparkles: *Highlights*
• {Most impactful change — plain text, no ticket ID or link}
• {Second highlight}
• {Third highlight}
• {Fourth highlight}
• {Fifth highlight}

:boom: *Breaking Changes*
• {Description} — {TICKET} {JIRA_BASE_URL}{TICKET}

:gift: *New Features*
• {Description} — {TICKET} {JIRA_BASE_URL}{TICKET}
• {Description} — {TICKET} {JIRA_BASE_URL}{TICKET}

:chart_with_upwards_trend: *Improvements*
• {Description} — {TICKET} {JIRA_BASE_URL}{TICKET}

:bug: *Bug Fixes*
• {Description} — {TICKET} {JIRA_BASE_URL}{TICKET}

:shield: *Security*
• {Description}

:warning: *Deprecations*
• {Description} — {TICKET} {JIRA_BASE_URL}{TICKET}

:wrench: *Maintenance*
• {X} code quality improvements, {Y} dependency updates

https://github.com/{REPO}/releases/tag/{tag}
```

**Slack formatting rules:**

- Include a `:sparkles: *Highlights*` section — curate 3-5 plain-text one-liners of the most impactful changes across all categories. Prioritize user-facing features, then impactful bug fixes, then notable improvements. Exclude maintenance items from highlights.
- List features, improvements, and bug fixes individually — one bullet per PR
- Use em-dash (`—`) to separate description from ticket reference
- Item format: `• {Description} — {TICKET} {JIRA_BASE_URL}{TICKET}`
- Items without Jira tickets: `• {Description}` (no link)
- Do NOT include PR links (`#123`) in Slack items — only Jira ticket references
- Do NOT include `@contributor` names in Slack items
- Do NOT include domain sub-groupings under New Features — use a flat list
- Condense Maintenance to a single summary: `• {X} code quality improvements, {Y} dependency updates`
- Omit the New Contributors section from Slack — it appears in markdown/GitHub only
- Omit empty sections
- No CSV data or file paths — content ready to paste into Slack
- Use emoji prefixes: `:sparkles:` `:boom:` `:gift:` `:chart_with_upwards_trend:` `:bug:` `:shield:` `:warning:` `:wrench:`
- Bullet points with `•` character
- Footer: bare URL to the GitHub release

### Step 5: Preview and Confirm

Before writing any files or publishing, show a preview and ask for confirmation. Match the pattern from `/pr` and `/commit`.

1. **Show markdown preview** — first ~30 lines of the formatted markdown output
2. **Show Slack preview** — first ~15 lines of the Slack mrkdwn output (unless Slack is skipped)
3. **List ALL outputs** with their targets, marking each as **✓ active** or **⊘ skipped** based on opt-out flags:
   - Local: `./releases/release-notes-{version}.md` (always ✓)
   - Local: `./releases/release-notes-{version}.csv` (if format is `both` or `csv` ✓)
   - Local: `./releases/release-notes-{version}.slack.txt` (unless `--no-slack` or `--local-only`)
   - Notion: "Create row in Release Notes database" (unless `--no-notion` or `--local-only`)
   - GitHub: "Update release body for {tag}" (unless `--no-publish` or `--local-only`)
4. **Ask for confirmation** before proceeding:
   - "Ready to generate? [Y/modify/cancel]"
   - Allow the user to request changes before writing

### Step 6: Save Files

Save all local files to `./releases/` in the current working directory:

- `release-notes-{version}.md` (always, unless format is `csv` only)
- `release-notes-{version}.csv` (if format is `both` or `csv`)
- `release-notes-{version}.slack.txt` (unless `--no-slack` or `--local-only`)

### Step 7: Publish to GitHub — unless `--no-publish` or `--local-only`

Update the GitHub release body with the formatted markdown:

```bash
gh release edit <tag> --notes-file ./releases/release-notes-{version}.md
```

Confirm the update succeeded and report the release URL.

### Step 8: Save to Notion — unless `--no-notion` or `--local-only`

**If Notion MCP is available (`mcp__plugin_Notion_notion__notion-search`):**

1. **Search** for an existing "Release Notes" database:
   - Use `notion-search` to find a database titled "Release Notes"

2. **If database found:** Create a new row with these properties:
   - `Version` (title) — e.g., "v104"
   - `Date` (date) — release date
   - `Status` (select) — "Published" if GitHub publish is active, otherwise "Draft"
   - `Features` (number) — count of new features
   - `Bug Fixes` (number) — count of bug fixes
   - `GitHub Release` (url) — link to GitHub release
   - `Summary` (rich text) — brief summary line

   Add the full formatted markdown as the page body content (including all sections: Breaking Changes, New Features, Improvements, Bug Fixes, Security, Deprecations, Maintenance, and New Contributors).

3. **If database NOT found:** Prompt the user for a parent page, then create the database with the schema above using `notion-create-database`. Then create the first row.

4. Return the Notion page URL.

**If Notion MCP is NOT available:**

- Skip Notion save
- Inform user: "Notion MCP not available — files saved locally but not to Notion"

## Output

Present summary when complete:

> "Release notes for {version} formatted:
>
> - Local: `./releases/release-notes-{version}.md` and `.csv`
> - Slack: `./releases/release-notes-{version}.slack.txt` ✓ / skipped
> - Notion: {url} ✓ / skipped
> - GitHub: Release updated — {release_url} ✓ / skipped
>
> Summary: X features, Y bug fixes, Z maintenance items"
