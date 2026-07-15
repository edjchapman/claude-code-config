---
name: project-setup
description: Set up or bootstrap a project with the claude-code-config tooling — setup-project.sh, install-tooling.sh, the layered hooks setup, and the new-repo runbook. Use when installing this config into a repo, running the setup scripts, vendoring the make-check tooling, or bootstrapping a new project.
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

## Bootstrap a brand-new repo

For a greenfield repo, run in this order (full end-to-end runbook — manifest
hygiene, standard files, remote creation, merge policy, `main-protection`
ruleset, strict commit style — lives in the maintainer's global `~/.claude/CLAUDE.md`):

1. **Layered setup** — `setup-project.sh <type>`, then `install-tooling.sh <type>`
   (omit `--hooks`; see the gotcha above), then a `.pre-commit-config.yaml` with a
   `repo: local` hook running `make check`.
2. **Wire `stack-check`** in the vendored Makefile to the stack's fmt + lint + test;
   run `make check` green before the first commit.
3. **Standard files** — README, LICENSE, CONTRIBUTING, PR template, dependabot, CI.
4. **Create the remote** — `gh repo create <Name> --public --source . --push`.
5. **Prove the loop** — land the first change via branch → PR → checks → squash-merge.

## Related

- **Global install** (symlinks `agents/`, `skills/`, `rules/`, `settings.json` into
  `~/.claude/`): `<repo>/scripts/setup-global.sh`.
- **MkDocs style layer**: `<repo>/scripts/install-mkdocs-style.sh` (wrapped by the
  `/mkdocs-style` skill).
- Full script + flag reference: [`docs/architecture.md`](../../docs/architecture.md).
