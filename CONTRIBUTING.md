# Contributing

Thanks for your interest! This is a single-maintainer personal config repo, but PRs are welcome — especially for fixes to shell scripts, JSON template gaps, or doc improvements.

## Quick setup

```bash
git clone https://github.com/edjchapman/claude-code-config.git
cd claude-code-config

# Install pre-commit hooks (one-time)
pip install pre-commit
pre-commit install

# Optional: install commit-msg hook too (only relevant if you ever start
# enforcing per-commit conventional-commits; right now only PR titles are
# validated in CI)
# pre-commit install --hook-type commit-msg
```

`pre-commit install` writes a `.git/hooks/pre-commit` script that runs the hooks defined in `.pre-commit-config.yaml` on every `git commit`. Hooks formatted-only fixes are applied automatically; lint failures block the commit until resolved.

To run the full hook suite manually:

```bash
pre-commit run --all-files
```

To update pinned hook versions occasionally:

```bash
pre-commit autoupdate
```

## Architecture & conventions

Read [CLAUDE.md](./CLAUDE.md) for the full architecture: how agents, commands, skills, rules, hooks, and templates fit together. Don't duplicate that content here.

## Commit & PR conventions

- **PR titles** must follow [Conventional Commits](https://www.conventionalcommits.org/) format. The `lint-pr` workflow validates this on every PR. Allowed types: `feat`, `fix`, `chore`, `docs`, `style`, `refactor`, `test`, `ci`, `perf`. Scope is optional but encouraged (e.g. `feat(skills):`, `fix(scripts):`).
- The repo uses **squash merge** — the PR title becomes the commit subject on `main`, the PR body becomes the commit body.
- Individual commits on a PR branch do not need to follow conventional-commits format. Optimize for review legibility (logical commits, clear messages) rather than for the final squash.
- Branch names: `<type>/<short-description>` (e.g. `feat/add-go-mcp-template`, `chore/upgrade-actions`). No ticket prefix is needed — there's no ticket system on this repo.

## CI checks

Pull requests must pass:

- `validate-json` — JSON parse + merge dry-run for every template
- `shellcheck` — at warning severity
- `check-duplicates` — no name collisions across `agents/`, `commands/`, `skills/`
- `markdownlint` — `.md` files against `.markdownlint.json`
- `actionlint` — workflow YAML
- `lint-pr` — conventional-commits PR title format

Branch protection on `main` requires all of these to be green. There are no required reviewers (solo-friendly setup).

## Maintainer setup

One-time setup commands (recorded so they're reproducible after a repo migration). You don't need to run these as a contributor — they're applied to the GitHub repo, not the source tree.

```bash
# Auto-delete merged branches
gh api -X PATCH repos/edjchapman/claude-code-config -f delete_branch_on_merge=true

# Squash-only merges
gh api -X PATCH repos/edjchapman/claude-code-config \
  -f allow_squash_merge=true \
  -f allow_merge_commit=false \
  -f allow_rebase_merge=false \
  -f squash_merge_commit_title=PR_TITLE \
  -f squash_merge_commit_message=PR_BODY

# Branch protection (see plan file for the full --input JSON payload)
# Repo topics, wiki disable, Dependabot security alerts — likewise.
```

The full set of commands lives in the plan file referenced from the WS6/Chunk 5 commit; this section is the maintainer's reminder, not the canonical source.

## Releases

Releases are handled by [release-please](https://github.com/googleapis/release-please). Don't manually bump version numbers or write `CHANGELOG.md` entries — release-please does both automatically based on conventional-commit prefixes on `main`:

- `feat:` commits → minor version bump
- `fix:` commits → patch version bump
- `feat!:` or `BREAKING CHANGE:` footer → major bump
- Other types (`chore`, `docs`, `style`, etc.) → no version bump; included in changelog as housekeeping

When release-please has accumulated changes to release, it opens a "chore: release X.Y.Z" PR. Merging that PR tags the release and updates `.claude-plugin/plugin.json`'s `version` field.

## Reporting bugs / asking questions

- **Bug:** open an [Issue](https://github.com/edjchapman/claude-code-config/issues) with a reproduction.
- **Question / idea:** open a [Discussion](https://github.com/edjchapman/claude-code-config/discussions) (or a draft Issue if Discussions are disabled).
- **Security:** see [SECURITY.md](./SECURITY.md).
