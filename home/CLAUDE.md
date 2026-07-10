# Global behavioural rules

Symlinked to `~/.claude/CLAUDE.md` by `scripts/setup-global.sh`. Loaded by Claude Code in every session, regardless of working directory. Keep this file for **cross-project** rules — anything project-specific belongs in that project's own `CLAUDE.md`.

## Capturing deferred follow-ups

When you notice a non-time-bound follow-up mid-session (a validator worth building, a pattern worth capturing, a learning to revisit), give it a **durable home before** writing _"deferred to future sessions"_ in your reply — chat narrative dies with context expiry, the rest survive.

- **Cross-session / personal backlog** — call `/later` with `--category Learn`/`Do`/`Research`/`Read`. Writes to `~/Reference/Later/<Category>/`, surfaced when `/later` next runs.
- **Repo TODO without a trigger** — inline comment in the relevant file (Makefile / script / markdown). Survives via git; visible when next editing that file.
- **Memory-worthy rule or pattern** — write a new `feedback_*.md` to `~/.claude/projects/<slug>/memory/` (cross-session, but **not git-backed**). For rules that should apply globally across all projects, add a section to _this_ file instead — git-backed via `claude-code-config`.

Default: pick the most durable home that matches the scope. A few seconds invoking `/later` (or adding two lines here) beats a silently-lost learning.

## Applying the shared `claude-code-config` tooling

When vendoring the tooling into a repo that should keep my global git-hooks dispatcher active (`~/.config/git/hooks` runs ggshield secret-scan + `pre-commit`/ruff):

- **`--tooling` implies `--hooks`.** `setup-project.sh <type> --tooling` calls `install-tooling.sh --hooks`, which sets a **repo-local** `core.hooksPath .githooks`. That **shadows the global dispatcher**, silently dropping ggshield + ruff on commit. To keep them, run the layers separately and **omit `--hooks`** (`setup-project.sh <type>`, then `install-tooling.sh <type>`), and add `make check` as a local hook in the repo's `.pre-commit-config.yaml` so the gate still runs on commit.
- **Don't blanket-ignore `.claude/`.** A repo _commits_ `.claude/settings.json` + `.claude/hooks/` (the Claude-on-web bootstrap from `--tooling`); `.gitignore` only the personal bits — `.claude/{agents,skills,rules}` (plus `.claude/commands` on older installs), `settings.local.json`, `.mcp.json`.

## Bootstrapping a new repo (end-to-end)

Validated on `AiEngineering` (2026-07-10). GitHub account: `edjchapman`. Run from the project root, in this order:

1. **Layered setup** — `setup-project.sh <type>`, then `install-tooling.sh <type>` (omit `--hooks`; see the section above), then a `.pre-commit-config.yaml` with a `repo: local` hook running `make check` (`language: system`, `pass_filenames: false`).
2. **Wire `stack-check`** in the vendored Makefile to the stack's fmt + lint + test (Rust: `cargo fmt --check && cargo clippy --all-targets -- -D warnings && cargo test`). Run `make check` green before the first commit.
3. **Manifest hygiene** — package name per ecosystem convention (Rust packages: kebab-case), plus description / license / readme / repository fields; pin the minimum toolchain (e.g. `rust-version`) to what's installed.
4. **Standard files** — README (quick start, `make check` workflow, CI badge), MIT LICENSE, CONTRIBUTING.md (branch → PR → squash flow), `.github/PULL_REQUEST_TEMPLATE.md`, `.github/dependabot.yml` (weekly; package ecosystem with minor+patch grouped, plus `github-actions`). Add toolchain-install + cache steps to the vendored `check.yml` (Rust: `dtolnay/rust-toolchain@stable` with rustfmt/clippy, `Swatinem/rust-cache@v2`).
5. **Create the remote** — `gh repo create <Name> --public --source . --push`, then `gh repo edit --add-topic ...`.
6. **Merge policy** — `gh api -X PATCH repos/<owner>/<repo>`: squash-only (`allow_merge_commit=false`, `allow_rebase_merge=false`), `delete_branch_on_merge=true`, `allow_auto_merge=true`, `squash_merge_commit_title=PR_TITLE`, `squash_merge_commit_message=PR_BODY`.
7. **`main-protection` ruleset** — require PR (0 approvals, `allowed_merge_methods: ["squash"]`), required status checks `make check` + `validate PR title` (these are job **names**, not workflow names — renaming a job orphans the requirement), strict up-to-date policy, linear history, block deletion + force-push, and a `RepositoryRole` id 5 (admin) always-bypass so a solo maintainer is never locked out.
8. **Promote commit style to strict immediately** — a brand-new repo has no legacy runway to honour: add `--strict` in `.github/workflows/commit-style.yml` and `.githooks/commit-msg`. Under squash-merge the PR title is the permanent commit subject; branch commits are disposable WIP.
9. **Prove the loop** — land the process change itself via branch → PR → checks → `gh pr merge --squash`, then `git switch main && git pull --prune && git branch -D <branch>` (squash merges need `-D`; ancestry never records the merge).
