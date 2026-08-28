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

## The GitGuardian secret scan (ggshield) — cost model and failure mode

The global pre-commit hook (`~/.config/git/hooks/pre-commit`, chezmoi-managed) runs
`ggshield secret scan pre-commit` before **every commit in every repo on this machine**,
against one workspace budget of **10,000 API calls on a rolling 30-day window**. It is
shared: exhausting it in one repo blocks commits in all of them, and it recovers only as
old usage ages out — there is no top-up.

**A failed scan is not a detected secret.** Only exit code **1** means secrets were found.
Quota exhaustion exits **128**, auth failure **3**, server-unreachable **4**. The hook used
to print *"ggshield detected secrets in your commit"* on any non-zero exit, which sent
agents sanitising files that were never dirty; it now names the real cause and prints the
live quota. **Before acting on any ggshield failure, run `ggshield quota`.**

**The cost model** (measured 2026-08-28; billing confirmed in [GitGuardian's
docs](https://docs.gitguardian.com/api-docs/usage-and-quotas)):

| Operation | Cost |
|---|---|
| One `git commit` (any size up to 20 changed files) | **1 unit** |
| A commit of N changed files | `ceil(N / 20)` units |
| `ggshield secret scan repo .` (full history, e.g. `make audit`) | **hundreds** — ~417 for a 996-commit repo |

Quota is billed **per API request, not per document**: `/multiscan` carries up to 20
documents for 1 unit. So ordinary commits are cheap — 447 real scans across one busy
month cost 482 units, under 5% of the budget. The expensive thing is *scan mode*, not
volume: **one full-history scan costs as much as ~400 commits.** Treat `secret scan repo`
as a deliberate, occasional act, never a routine gate.

**Open question — most of the spend is still unexplained.** The 2026-08-28 audit
accounted for only ~10–15% of a saturated 10,000-unit window: commits across every live
worktree came to 482 units, and no other local consumer exists (no ggshield in CI, no
GitGuardian IDE plugin, no cron/launchd job, no `pre-push` hook — all checked and
eliminated). The remaining ~8,500 units need GitGuardian's own **API-usage-over-time**
view on the dashboard, which the CLI cannot query (the key is `scan`-scope only). Check
there before assuming commit volume is the problem — the measurement says it is not.

**Never work around exhaustion with `git commit --no-verify`** — in repos whose
`.githooks/pre-commit` also runs a validation battery, that bypasses the battery too.
Bypassing needs Ed's explicit, per-commit approval, and `make check` must then be run by
hand. Where a repo uses the `pre-commit` framework, `SKIP=ggshield git commit` skips only
that hook and is the safer lever.

## Applying the tooling & bootstrapping repos

The `--hooks`/`--tooling` gotcha, `.gitignore` hygiene, and the full end-to-end new-repo runbook (manifest hygiene, standard files, remote creation, merge policy, `main-protection` ruleset, strict commit style, prove-the-loop) live in the **`project-setup` skill** — invoked on demand rather than loaded every session. Reach for it when installing this config into a repo or bootstrapping a new one.
