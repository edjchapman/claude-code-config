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
