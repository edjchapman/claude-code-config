---
name: project-setup
description: Install this config into a repo or bootstrap a new one — setup-project.sh, install-tooling.sh, the layered hooks setup, the new-repo runbook. Use when running the setup scripts or vendoring the tooling.
---

# Project Setup

How to apply this repo's tooling to a project. Substitute `<repo>` with wherever
`claude-code-config` is cloned (commonly `~/Development/claude-code-config/` — keep a
single clone; the global symlinks and any dev work should point at the same one).
Full reference for every script and flag is
in [`docs/architecture.md`](../../docs/architecture.md) ("Key Scripts").

## Apply the config to an existing project

Run from the target project's root:

```bash
# Permissions + MCP templates for your stack (generates .claude/settings.local.json, .mcp.json)
<repo>/scripts/setup-project.sh <template> [template2...]

# Inspect first
<repo>/scripts/setup-project.sh --list            # available templates
<repo>/scripts/setup-project.sh --dry-run django  # preview changes
<repo>/scripts/setup-project.sh --check django    # check drift + symlinks
<repo>/scripts/setup-project.sh --status          # current config state
```

## The `--hooks` / `--tooling` gotcha (read before using `--tooling`)

`setup-project.sh <type> --tooling` vendors the hard-tooling layer (Makefile,
validators, git hooks, CI) by calling `install-tooling.sh --hooks`. **That sets a
repo-local `core.hooksPath .githooks`, which shadows a global git-hooks
dispatcher** (e.g. `~/.config/git/hooks` running ggshield secret-scan + ruff),
silently dropping those checks on commit.

To keep a global dispatcher active, **run the layers separately and omit `--hooks`**:

```bash
<repo>/scripts/setup-project.sh <type>            # Claude layer (no --tooling)
<repo>/scripts/install-tooling.sh <type>          # tooling layer, WITHOUT --hooks
```

Then add `make check` as a `repo: local` hook in the project's
`.pre-commit-config.yaml` (`language: system`, `pass_filenames: false`) so the
quality gate still runs on commit.

**`.gitignore` hygiene**: commit `.claude/settings.json` + `.claude/hooks/` (the
Claude-on-web bootstrap from `--tooling`); ignore only the personal bits —
`.claude/{agents,skills,rules}`, `settings.local.json`, `.mcp.json`. Don't
blanket-ignore `.claude/`.

## Bootstrap a brand-new repo (end-to-end)

For a greenfield repo, run from the project root in this order. Validated on
`AiEngineering` (2026-07-10). GitHub account: `edjchapman`.

1. **Layered setup** — `setup-project.sh <type>`, then `install-tooling.sh <type>` (omit `--hooks`; see the gotcha above), then a `.pre-commit-config.yaml` with a `repo: local` hook running `make check` (`language: system`, `pass_filenames: false`).
2. **Wire `stack-check`** in the vendored Makefile to the stack's fmt + lint + test (Rust: `cargo fmt --check && cargo clippy --all-targets -- -D warnings && cargo test`). Run `make check` green before the first commit.
3. **Manifest hygiene** — package name per ecosystem convention (Rust packages: kebab-case), plus description / license / readme / repository fields; pin the minimum toolchain (e.g. `rust-version`) to what's installed.
4. **Standard files** — README (quick start, `make check` workflow, CI badge), MIT LICENSE, CONTRIBUTING.md (branch → PR → squash flow), `.github/PULL_REQUEST_TEMPLATE.md`, `.github/dependabot.yml` (weekly; package ecosystem with minor+patch grouped, plus `github-actions`). Add toolchain-install + cache steps to the vendored `check.yml` (Rust: `dtolnay/rust-toolchain@stable` with rustfmt/clippy, `Swatinem/rust-cache@v2`).
5. **Create the remote** — `gh repo create <Name> --public --source . --push`, then `gh repo edit --add-topic ...`.
6. **Merge policy** — `gh api -X PATCH repos/<owner>/<repo>`: squash-only (`allow_merge_commit=false`, `allow_rebase_merge=false`), `delete_branch_on_merge=true`, `allow_auto_merge=true`, `squash_merge_commit_title=PR_TITLE`, `squash_merge_commit_message=PR_BODY`.
7. **`main-protection` ruleset** — require PR (0 approvals, `allowed_merge_methods: ["squash"]`), required status checks `make check` + `validate PR title` (these are job **names**, not workflow names — renaming a job orphans the requirement), strict up-to-date policy, linear history, block deletion + force-push, and a `RepositoryRole` id 5 (admin) always-bypass so a solo maintainer is never locked out.
8. **Promote commit style to strict immediately** — a brand-new repo has no legacy runway to honour: add `--strict` in `.github/workflows/commit-style.yml` and `.githooks/commit-msg`. Under squash-merge the PR title is the permanent commit subject; branch commits are disposable WIP.
9. **Prove the loop** — land the process change itself via branch → PR → checks → `gh pr merge --squash`, then `git switch main && git pull --prune && git branch -D <branch>` (squash merges need `-D`; ancestry never records the merge).

## Related

- **Global install** (symlinks `agents/`, `skills/`, `rules/` into `~/.claude/`
  and mirrors `settings.json` — ADR-0002): `<repo>/scripts/setup-global.sh`.
- **MkDocs style layer**: `<repo>/scripts/install-mkdocs-style.sh` (wrapped by the
  `/mkdocs-style` skill).
- Full script + flag reference: [`docs/architecture.md`](../../docs/architecture.md).
