# Global behavioural rules

Symlinked to `~/.claude/CLAUDE.md` by `scripts/setup-global.sh`. Loaded by Claude Code in every session, regardless of working directory. Keep this file for **cross-project** rules — anything project-specific belongs in that project's own `CLAUDE.md`.

## Capturing deferred follow-ups

When you notice a non-time-bound follow-up mid-session (a validator worth building, a pattern worth capturing, a learning to revisit), give it a **durable home before** writing _"deferred to future sessions"_ in your reply — chat narrative dies with context expiry, the rest survive.

- **Cross-session / personal backlog** — call `/later` with `--category Learn`/`Do`/`Research`/`Read`. Writes to `~/Reference/Later/<Category>/`, surfaced when `/later` next runs.
- **Repo TODO without a trigger** — inline comment in the relevant file (Makefile / script / markdown). Survives via git; visible when next editing that file.
- **Memory-worthy rule or pattern** — write a new `feedback_*.md` to `~/.claude/projects/<slug>/memory/` (cross-session, but **not git-backed**). For rules that should apply globally across all projects, add a section to _this_ file instead — git-backed via `claude-code-config`.

Default: pick the most durable home that matches the scope. A few seconds invoking `/later` (or adding two lines here) beats a silently-lost learning.

## Writing code

- Comments: only where the "why" isn't obvious. Never restate what code does.

## The GitGuardian secret scan (ggshield)

The global **pre-push** hook (`~/.config/git/hooks/pre-push`, chezmoi-managed) scans the
commits about to leave the machine, in every repo, against one shared workspace budget of
10,000 API calls on a rolling 30-day window — exhausting it in one repo blocks pushes in
all of them, and it recovers only as old usage ages out. (It moved from pre-commit in
Dotfiles#159: per-commit scanning billed every amend and rejected attempt. Individual
repos may still carry their own per-commit ggshield hook via the `pre-commit` framework.)

**A failed scan is not a detected secret.** Only exit code 1 means secrets were found;
quota exhaustion exits 128, auth failure 3, server-unreachable 4. **Run `ggshield quota`
before acting on any ggshield failure** — on the old hook's message, which said "detected
secrets" for every non-zero exit, agents sanitised files that were never dirty.

**Cost** (measured 2026-08-28; billing is per API _request_, not per document — `/multiscan`
carries 20 documents for one unit): a commit costs **1 unit**, or `ceil(files / 20)`.
`ggshield secret scan repo` costs **hundreds** — ~417 on a 996-commit repo. A busy month of
commits came to under 5% of the budget, so cutting commit volume buys almost nothing and
costs real safety; the expensive thing is scan _mode_. Treat full-history scans as
deliberate and occasional, never a routine gate. If the budget is gone, suspect those (or
check GitGuardian's dashboard) before blaming commit volume.

**Never bypass with `git commit --no-verify`** where a repo's `.githooks/pre-commit` also
runs a validation battery — that skips the battery too. It needs Ed's explicit per-commit
approval, with `make check` then run by hand. Under the `pre-commit` framework,
`SKIP=ggshield git commit` skips only that hook and is the safer lever.

**When quota exhaustion blocks a push** (exit 128 — which can persist for weeks):
`git push --no-verify` skips only the secret scan, since the global pre-push hook is the
only pre-push check; per-commit gitleaks and GitGuardian's GitHub App still cover the
range. It needs Ed's explicit per-push approval — agents must stop and ask, never run it
unprompted.

## Applying the tooling & bootstrapping repos

The `--hooks`/`--tooling` gotcha, `.gitignore` hygiene, and the full end-to-end new-repo runbook (manifest hygiene, standard files, remote creation, merge policy, `main-protection` ruleset, strict commit style, prove-the-loop) live in the **`project-setup` skill** — invoked on demand rather than loaded every session. Reach for it when installing this config into a repo or bootstrapping a new one.
