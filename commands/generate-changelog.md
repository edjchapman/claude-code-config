Generate a changelog from commits since the last tag.

## Arguments

`$ARGUMENTS`

- `--from <ref>`: Start from specific tag/commit (default: latest tag)
- `--to <ref>`: End at specific ref (default: HEAD)
- `--format <type>`: Output format: `md`, `json`, `keep-a-changelog` (default: md)
- `--version <version>`: Version number for the changelog (default: auto-detect from tag)
- `--include-all`: Include all commits (default: exclude merge commits and dependabot)
- Examples: `/generate-changelog`, `/generate-changelog --from v1.0.0 --to v1.1.0`, `/generate-changelog --format keep-a-changelog`

## Step 1: Determine Version Range

```bash
# Get latest tag
git describe --tags --abbrev=0

# Get commits since last tag
git log $(git describe --tags --abbrev=0)..HEAD --oneline
```

**If `--from` provided:**
```bash
git log {from}..{to} --oneline
```

## Step 2: Fetch Commit Information

```bash
# Get detailed commit info
git log {from}..{to} --pretty=format:"%H|%s|%an|%ae|%ai" --no-merges

# Include PR numbers if available
git log {from}..{to} --pretty=format:"%H|%s" | grep -oE '#[0-9]+'
```

## Step 3: Categorize Commits

Parse commits using conventional commit prefixes:

| Prefix | Category |
|--------|----------|
| `feat:` | Features |
| `fix:` | Bug Fixes |
| `perf:` | Performance |
| `refactor:` | Refactoring |
| `docs:` | Documentation |
| `test:` | Tests |
| `chore:` | Maintenance |
| `ci:` | CI/CD |
| `security:` | Security |
| `breaking:` or `BREAKING CHANGE:` | Breaking Changes |
| `deps:` or `build(deps):` | Dependencies |

**Fallback for non-conventional commits:**
- Analyze commit message content to categorize
- Group unlabeled commits under "Other Changes"

## Step 4: Extract Jira Tickets

**Pattern matching:**
- `BIL-XXXX`, `ABC-123`, etc. from commit messages and branch names

**If Jira MCP is available (`mcp__plugin_atlassian_atlassian__getJiraIssue`):**
- Fetch ticket summaries for context
- Link to Jira issues in changelog

## Step 5: Get Contributor Information

```bash
# Unique contributors
git log {from}..{to} --format="%an" | sort -u
```

**If GitHub MCP is available (`mcp__plugin_github_github__*`):**
- Fetch PR authors and reviewers
- Link to GitHub profiles

## Step 6: Generate Changelog

### Markdown Format (default)

```markdown
# Changelog

## [{version}] - {date}

### Breaking Changes
- **{scope}**: {description} ([#{pr}]({pr_url})) - @{author}

### Features
- **{scope}**: {description} ([#{pr}]({pr_url})) - @{author}
  - Related: [{ticket}]({jira_url})

### Bug Fixes
- **{scope}**: {description} ([#{pr}]({pr_url})) - @{author}

### Performance
- {description}

### Documentation
- {description}

### Maintenance
- Dependency updates: {list}

---

### Contributors
- @contributor1
- @contributor2

**Full Changelog**: [{from}...{to}]({compare_url})
```

### Keep-a-Changelog Format

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [{version}] - {date}

### Added
- {new features}

### Changed
- {changes}

### Deprecated
- {deprecations}

### Removed
- {removals}

### Fixed
- {bug fixes}

### Security
- {security fixes}
```

### JSON Format

```json
{
  "version": "{version}",
  "date": "{date}",
  "categories": {
    "breaking": [],
    "features": [],
    "fixes": [],
    "performance": [],
    "documentation": [],
    "maintenance": []
  },
  "contributors": [],
  "commits": {
    "from": "{from_ref}",
    "to": "{to_ref}",
    "count": 0
  }
}
```

## Step 7: Save Output

Save to appropriate file:
- `CHANGELOG.md` (append/update)
- `releases/CHANGELOG-{version}.md`
- `changelog.json`

## Output

Present summary:
> "Generated changelog for {version}:
> - {n} features, {m} bug fixes, {p} other changes
> - {c} contributors
> - Saved to: {output_file}"

## Guidelines

- Group related commits (e.g., frontend + backend for same feature)
- Highlight breaking changes prominently at the top
- Link to PRs and issues where possible
- Keep descriptions concise but meaningful
- Strip conventional commit prefixes from displayed text
- Exclude automated commits (dependabot, renovate) unless `--include-all`
- Follow the repository's existing changelog format if one exists
