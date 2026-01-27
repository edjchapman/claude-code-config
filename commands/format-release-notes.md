# Format Release Notes

Format GitHub release notes for Jira and stakeholder communication.

## Arguments

```
/format-release-notes [options] [format] [version]
```

**Options:**
- `--fetch <tag>`: Auto-fetch release notes from GitHub (e.g., `--fetch v103`)
- `--latest`: Fetch the most recent release automatically
- `--notion`: Save formatted notes to Notion after generating

**Positional:**
- `format`: `md` (default), `csv`, or `both`
- `version`: Override auto-detected version (e.g., `v103`)

**Examples:**
- `/format-release-notes --latest` - Fetch and format most recent release
- `/format-release-notes --fetch v103 both` - Fetch v103, output md and csv
- `/format-release-notes --latest --notion` - Fetch latest, save to Notion
- `/format-release-notes md v104` - Format pasted notes as v104

## Instructions

### Step 0: Determine Input Source

**If `--fetch <tag>` provided:**
```bash
gh release view <tag> --json body,tagName,name -q '{body: .body, tag: .tagName, name: .name}'
```

**If `--latest` provided:**
```bash
# Get latest release tag
gh release list --limit 1 --json tagName -q '.[0].tagName'
# Then fetch that release
gh release view <tag> --json body,tagName,name -q '{body: .body, tag: .tagName, name: .name}'
```

**If no input provided and no flags:**
Present interactive menu:
> "No release notes provided. Would you like me to:
> 1. **Fetch from a specific release tag** - I'll ask for the tag name
> 2. **Fetch the latest release** - I'll grab the most recent one
> 3. **Paste your own release notes** - Provide raw notes to format"

### Step 1: Parse Release Notes
Parse the release notes (from GitHub fetch or user-provided input)

### Step 2: Extract Version
Extract the version from the release title or tag

### Step 3: Categorize PRs
Categorize each PR into sections

### Step 4: Format and Save
Format output and save to current working directory

### Jira Configuration

- **Base URL**: `https://builtai.atlassian.net/browse/`
- **Ticket Pattern**: `BIL-XXXX` (extract from PR title prefix)

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

Omit empty sections from output.

### Formatting Rules

- Link tickets: `[BIL-1234](https://builtai.atlassian.net/browse/BIL-1234)`
- Link PRs: `[#123](https://github.com/BuiltAI/clarion_app/pull/123)`
- Group related PRs (backend + frontend) on one line
- Include contributors: `@username`
- Strip conventional commit prefixes (`feat:`, `fix:`, `chore:`)
- PRs without ticket IDs: List under "Other" within their category
- Dependabot PRs: Group under Maintenance as "Dependency Updates"
- Revert PRs: Note as "(reverted)" on the original PR line if both present

### Output

**Markdown** (`release-notes-{version}.md`):

```markdown
# Release {version}

## Summary

- X new features
- X bug fixes
- X maintenance items

## Breaking Changes

- [BIL-1234](https://builtai.atlassian.net/browse/BIL-1234) Remove deprecated `/api/v1/tenants` endpoint [#456](url) @dev

## New Features

### Portfolio

- [BIL-1111](url) Add custom ordering for tenants [#123](url) [#124](url) @dev1 @dev2

### Export/Import

- [BIL-2222](url) Admin export for projects and assets [#125](url) @dev3

## Bug Fixes

- [BIL-3333](url) Fix timezone handling in lease dates [#126](url) @dev4

## Maintenance

- Dependency Updates: [#130](url) [#131](url) [#132](url)
- [BIL-4444](url) Refactor tenant service [#127](url) @dev5
```

**CSV** (`release-notes-{version}.csv`):

```
Category,Ticket,Description,Contributors,PR Links
New Features,BIL-1111,Add custom ordering for tenants,@dev1 @dev2,#123 #124
Bug Fixes,BIL-3333,Fix timezone handling in lease dates,@dev4,#126
```

### Step 5: Save to Notion (if `--notion` flag)

**If Notion MCP is available (`mcp__plugin_Notion_notion__notion-create-pages`):**
- Create a new page with formatted release notes:
  - **Title**: "Release Notes - {version}"
  - **Content**: Full formatted markdown output
  - **Properties**: Version tag, release date, summary stats
- Return the Notion page URL

**If Notion MCP is NOT available:**
- Skip Notion save
- Inform user: "Notion MCP not available - files saved locally but not to Notion"

## Output

**Default:** Save to `./releases/release-notes-{version}.md` (and `.csv` if requested)

**With `--notion`:** Also create Notion page and return URL

Present summary:
> "Release notes for {version} formatted:
> - Local: `./releases/release-notes-{version}.md`
> - Notion: {url} (if --notion used)
>
> Summary: X features, Y bug fixes, Z maintenance items"

## User Input

$ARGUMENTS