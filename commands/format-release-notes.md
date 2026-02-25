# Release Notes

Generate a formatted GitHub release description from PRs merged between two tags.

## Arguments

`$ARGUMENTS`

- `<tag>`: The release tag to generate notes for (e.g., `v2.1.0`)
- `<previous-tag>`: Optional. The previous tag to diff against. Auto-detected if omitted.
- `--publish`: Update the GitHub release body immediately (default is draft/preview)
- `--no-deps`: Exclude dependency bumps (Dependabot, Renovate) and CI-only changes

**Examples:**

- `/format-release-notes v2.1.0` — auto-detect previous tag, preview as draft
- `/format-release-notes v2.1.0 v2.0.0` — explicit range, preview as draft
- `/format-release-notes v2.1.0 --publish` — generate and publish to GitHub release
- `/format-release-notes v2.1.0 --no-deps` — exclude dependabot/CI PRs

## Instructions

### Step 1: Resolve Project Context

Determine the repository and verify the tag exists.

```bash
# Get repo identifier
gh repo view --json nameWithOwner -q '.nameWithOwner'

# Verify tag exists
git tag -l "<tag>"
```

Store `REPO` (e.g., `octocat/my-project`) for use in later steps. If the tag doesn't exist, inform the user and stop.

### Step 2: Determine Tag Range

**If `<previous-tag>` provided:** Use both tags directly.

**If only `<tag>` provided:** Auto-detect the previous tag:

```bash
# Try: most recent release before this tag
gh release list --json tagName,isLatest --limit 20 -q '[.[] | select(.tagName != "<tag>")] | .[0].tagName'

# Fallback: previous tag by git history
git describe --tags --abbrev=0 "<tag>^"
```

Store `PREV_TAG` and `TAG` for use in the next step.

### Step 3: Fetch PRs Between Tags

Extract merged PRs from the tag range using git log:

```bash
# Get merge commits and squash-merge subjects between tags
git log <PREV_TAG>..<TAG> --pretty=format:"%s" --first-parent
```

Extract PR numbers from commit subjects:

- Merge commits: `Merge pull request #123 from ...`
- Squash merges: `Some description (#123)`

Then fetch PR details for each extracted number:

```bash
gh pr view <number> --json number,title,author,labels,url
```

Batch where possible using `gh api graphql` for efficiency if there are many PRs.

### Step 4: Categorize and Detect Issue Tracker

**Categorize** each PR by conventional commit prefix in the title:

| Prefix | Category |
|--------|----------|
| `feat:` / `feat(scope):` | New Features |
| `fix:` / `fix(scope):` | Bug Fixes |
| `perf:`, `improve:` | Improvements |
| `BREAKING CHANGE` or `!:` | Breaking Changes |
| `security:` | Security |
| `deprecate:` | Deprecations |
| `chore:`, `ci:`, `test:`, `docs:`, `refactor:`, `build:` | Maintenance |
| No prefix | Infer from labels/content, or place under "Other Changes" |

**Filtering:** If `--no-deps` is set, exclude:

- Dependabot / Renovate PRs (by author or title pattern)
- CI-only changes (`ci:` prefix, CI labels)

By default, all PRs are included.

**Auto-detect issue tracker** by scanning all PR titles:

1. Look for Jira-style patterns: `[A-Z]+-[0-9]+` (e.g., `BIL-1234`, `PROJ-456`)
2. If found, check `CLAUDE.md` for `atlassian.net` or `jira_base_url` to build links
3. If Jira URL found → `[PROJ-123](https://jira.example.com/browse/PROJ-123)`
4. If no Jira URL → show ticket ID as plain text, note this for the user
5. GitHub issue refs (`#123`) → `[#123](https://github.com/REPO/issues/123)`

### Step 5: Preview and Confirm

Format the release body as GitHub-flavored markdown and show a preview.

**Output format:**

```markdown
## Summary

**X** features · **Y** bug fixes · **Z** improvements · **W** maintenance

## Breaking Changes
- Description [#456](pr_url) @contributor — [PROJ-123](issue_url)

## New Features
- Description [#123](pr_url) @contributor

## Improvements
- Description [#125](pr_url) @contributor

## Bug Fixes
- Description [#126](pr_url) @contributor

## Security
- Description [#127](pr_url) @contributor

## Deprecations
- Description [#128](pr_url) @contributor

## Maintenance
- Description [#129](pr_url) @contributor

## New Contributors
- @user made their first contribution in [#N](pr_url)

**Full Changelog**: https://github.com/REPO/compare/PREV_TAG...TAG
```

**Formatting rules:**

- One PR per line — never group multiple PRs on a single line
- Strip conventional commit prefixes from display text (`feat:`, `fix:`, etc.)
- Include PR link and `@author` on every line
- Append issue tracker reference where detected (Jira ticket or GitHub issue)
- Omit empty sections entirely
- Separate sections with blank lines (no horizontal rules — GitHub renders them heavily)

**Show the user:**

1. The formatted markdown preview (first ~30 lines)
2. Ask how to proceed:
   - If `--publish` was passed: "Will update release body for `<TAG>` via `gh release edit`. Ready? [Y/edit/cancel]"
   - Otherwise (default): "How would you like to proceed? [publish/draft (default)/edit/cancel]"
     - **publish**: Update the GitHub release body now
     - **draft**: Output the full markdown without modifying the release (default if user just presses enter)
     - **edit**: Let the user request changes before finalizing
     - **cancel**: Abort

### Step 6: Publish

**If draft (default, or user chose "draft" at the prompt):** Output the full markdown and stop. Do not modify the GitHub release.

**If publish (`--publish` flag, or user chose "publish" at the prompt):** Update the GitHub release body:

```bash
# Write formatted notes to a temp file, then update the release
gh release edit <TAG> --notes-file <tempfile>
```

If the release doesn't exist yet for this tag, inform the user and suggest:

```bash
gh release create <TAG> --notes-file <tempfile>
```

Confirm success and report the release URL:

```
https://github.com/REPO/releases/tag/TAG
```

## Output

Present summary when complete:

> "Release notes for {TAG} generated:
>
> - PRs included: X (Y features, Z fixes, W maintenance)
> - GitHub release: {url} ✓ / draft only (default)
>
> Summary: X features, Y bug fixes, Z improvements, W maintenance"
