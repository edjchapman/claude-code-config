# Format Release Notes

Format GitHub release notes for Jira and stakeholder communication.

## Arguments

```
/format-release-notes [options] [format] [version]
```

**Options:**
- `--fetch <tag>`: Fetch release notes for a specific tag (e.g., `--fetch v103`)
- `--no-fetch`: Disable auto-fetch; prompt for pasted input instead
- `--notion`: Save formatted notes to Notion after generating

**Positional:**
- `format`: `both` (default), `md`, or `csv`
- `version`: Override auto-detected version (e.g., `v103`)

**Examples:**
- `/format-release-notes` - Fetch latest release, output md and csv
- `/format-release-notes --fetch v103` - Fetch specific tag, output md and csv
- `/format-release-notes --no-fetch md` - Paste notes manually, md only
- `/format-release-notes --notion` - Fetch latest, save to Notion

## Instructions

### Step 0: Determine Input Source

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
- Link PRs: `[#123](https://github.com/Built-AI/clarion_app/pull/123)`
- **One PR per line** — never group multiple PRs on the same line
- Same ticket can appear on multiple lines if it has multiple PRs
- Include contributors: `@username`
- Strip conventional commit prefixes (`feat:`, `fix:`, `chore:`)
- PRs without ticket IDs: List under their category without a ticket link
- Dependabot PRs: List individually under Maintenance > Dependency Updates with bump description
- Revert PRs: Note as "(reverted)" on the original PR line if both present
- Separate sections with `---` horizontal rules
- End with `**Full Changelog**: <GitHub compare URL>`

### Output

**Markdown** (`release-notes-{version}.md`):

```markdown
# Release Candidate {version}

## Summary

- **X new features** across Portfolio, Tenant/Lease, Unit Editor, etc.
- **X bug fixes**
- **X improvements**
- **X maintenance items** (including X dependency updates)

---

## Breaking Changes

- [BIL-1234](https://builtai.atlassian.net/browse/BIL-1234) Remove deprecated `/api/v1/tenants` endpoint [#456](https://github.com/Built-AI/clarion_app/pull/456) @dev

---

## New Features

### Portfolio

- [BIL-1111](https://builtai.atlassian.net/browse/BIL-1111) Description [#123](https://github.com/Built-AI/clarion_app/pull/123) @contributor

### Domain Area 2

- [BIL-2222](https://builtai.atlassian.net/browse/BIL-2222) Description [#125](https://github.com/Built-AI/clarion_app/pull/125) @dev1

---

## Bug Fixes

- [BIL-3333](https://builtai.atlassian.net/browse/BIL-3333) Description [#126](https://github.com/Built-AI/clarion_app/pull/126) @contributor

---

## Maintenance

### Code Quality

- [BIL-4444](https://builtai.atlassian.net/browse/BIL-4444) Description [#127](https://github.com/Built-AI/clarion_app/pull/127) @contributor

### Dependency Updates

- [#130](https://github.com/Built-AI/clarion_app/pull/130) Bump package-name X.X to Y.Y
- [#131](https://github.com/Built-AI/clarion_app/pull/131) Bump package-name X.X to Y.Y

---

**Full Changelog**: https://github.com/Built-AI/clarion_app/compare/prev-tag...current-tag
```

**CSV** (`release-notes-{version}.csv`):

```
Release,Category,Subcategory,Ticket,Ticket Link,Description,Contributors,PR Number,PR Link
v104,New Features,Portfolio,BIL-1111,https://builtai.atlassian.net/browse/BIL-1111,Description,@contributor,123,https://github.com/Built-AI/clarion_app/pull/123
v104,Bug Fixes,,BIL-3333,https://builtai.atlassian.net/browse/BIL-3333,Description,@contributor,126,https://github.com/Built-AI/clarion_app/pull/126
v104,Maintenance,Dependency Updates,,,Bump package-name X.X to Y.Y,@dependabot,130,https://github.com/Built-AI/clarion_app/pull/130
```

**CSV notes:**
- One row per PR (same ticket can appear on multiple rows if it has multiple PRs)
- Leave cells empty for optional fields (Subcategory, Ticket, Ticket Link) when not applicable
- Dependency updates use `@dependabot` as contributor

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

**Default:** Save to `./releases/release-notes-{version}.md` and `./releases/release-notes-{version}.csv`

**With `--notion`:** Also create Notion page and return URL

Present summary:
> "Release notes for {version} formatted:
> - Local: `./releases/release-notes-{version}.md` and `.csv`
> - Notion: {url} (if --notion used)
>
> Summary: X features, Y bug fixes, Z maintenance items"

## User Input

$ARGUMENTS
