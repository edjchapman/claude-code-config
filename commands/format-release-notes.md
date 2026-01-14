# Format Release Notes

Format GitHub release notes for Jira and stakeholder communication.

## Arguments

```
/format-release-notes [format] [version]
```

- `format`: `md` (default), `csv`, or `both`
- `version`: Override auto-detected version (e.g., `v103`)

If no arguments provided, output markdown only and auto-detect version from input.

## Instructions

1. Parse the release notes provided by the user (typically from GitHub's auto-generated notes)
2. Extract the version from the release title or tag
3. Categorize each PR into sections
4. Format output and save to current working directory

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

## User Input

$ARGUMENTS