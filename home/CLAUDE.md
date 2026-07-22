# Global behavioural rules

Symlinked to `~/.claude/CLAUDE.md` by `scripts/setup-global.sh`. Loaded by Claude Code in every session, regardless of working directory. Keep this file for **cross-project** rules — anything project-specific belongs in that project's own `CLAUDE.md`.

## Capturing deferred follow-ups

When you notice a non-time-bound follow-up mid-session (a validator worth building, a pattern worth capturing, a learning to revisit), give it a **durable home before** writing _"deferred to future sessions"_ in your reply — chat narrative dies with context expiry, the rest survive.

- **Cross-session / personal backlog** — call `/later` with `--category Learn`/`Do`/`Research`/`Read`. Writes to `~/Reference/Later/<Category>/`, surfaced when `/later` next runs.
- **Repo TODO without a trigger** — inline comment in the relevant file (Makefile / script / markdown). Survives via git; visible when next editing that file.
- **Memory-worthy rule or pattern** — write a new `feedback_*.md` to `~/.claude/projects/<slug>/memory/` (cross-session, but **not git-backed**). For rules that should apply globally across all projects, add a section to _this_ file instead — git-backed via `claude-code-config`.

Default: pick the most durable home that matches the scope. A few seconds invoking `/later` (or adding two lines here) beats a silently-lost learning.

## Applying the tooling & bootstrapping repos

The `--hooks`/`--tooling` gotcha, `.gitignore` hygiene, and the full end-to-end new-repo runbook (manifest hygiene, standard files, remote creation, merge policy, `main-protection` ruleset, strict commit style, prove-the-loop) live in the **`project-setup` skill** — invoked on demand rather than loaded every session. Reach for it when installing this config into a repo or bootstrapping a new one.
