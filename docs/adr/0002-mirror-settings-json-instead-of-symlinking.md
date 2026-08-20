# ADR-0002: Mirror `settings.json` into `~/.claude/` instead of symlinking it

**Status:** Accepted — 2026-08-20

## Context

`setup-global.sh` symlinked `~/.claude/settings.json` to the repo's
`settings.json`. Claude Code writes user-scope settings to that path at
runtime (`/model`, `/config` toggles, permission approvals), so any such
write from **any** project landed as a pending diff in this public repo.
The `model` key alone churned in and out of `settings.json` six times
since 2026-01-22; two guards (`check-settings-keys.py`, the settings-key
gloss check) detected the strays but nothing prevented them.

The documented escape hatch — personal settings in
`~/.claude/settings.local.json` — was proven inert by experiment
(2026-08-20): with different `model` values in the two files, a headless
session used the `settings.json` value; with no `model` in
`settings.json`, the session fell through to the account default, ignoring
the local file entirely. This matches the official settings docs, which
define a local scope only at project level (`.claude/settings.local.json`).
The consequences were live, not hypothetical: the maintainer's Fable pin
in the "personal layer" had never worked, the stray `"model": "fable"`
diff in the repo was the _actual_ pin, and the only user-scope file Claude
Code reads was the one it could not safely write to.

The repo already reached the same conclusion at project scope:
`setup-project.sh` deliberately does **not** symlink
`.claude/settings.json`.

## Decision

- `~/.claude/settings.json` is a **real file, mirrored** from the repo by
  `scripts/sync-global-settings.py` (invoked by `setup-global.sh`, re-runnable
  standalone). The `agents/`, `skills/`, and `rules/` symlinks remain —
  Claude Code never writes to those.
- **Strict mirror for managed keys**: keys the repo manages —
  `ALLOWED_KEYS` in `scripts/lib/settings_keys.py`, plus whatever the repo
  file carries — take the repo's value on every sync, including deletion of
  keys the repo drops (`RETIRED_KEYS` tombstones keys retired from
  `ALLOWED_KEYS` itself). Durable changes to managed keys are made in the
  repo, the same discipline the symlink enforced, minus the pollution.
- **`enabledPlugins` merges per entry**: repo-declared plugin entries mirror
  exactly (default-offs stay off); entries the repo does not declare —
  personal, account-gated plugins — are preserved.
- **Unmanaged keys are never touched**: `model`, `permissions`, and any
  future runtime write live only in the home file.
- **Drift is warned, never auto-healed**: a SessionStart hook
  (`settings-drift-check.sh`) prints a one-line warning when a sync would
  change anything. Silent mutation of user settings was considered and
  rejected.
- Hook command fallbacks anchor on `readlink ~/.claude/agents` (previously
  `readlink ~/.claude/settings.json`, which the unsymlink would have broken).

## Consequences

- Runtime settings writes never dirty the repo; personal, entitlement-gated
  keys finally have a home Claude Code actually reads.
- Live-update is lost for `settings.json`: a repo edit takes effect only
  after a sync (`setup-global.sh` or `sync-global-settings.py`); the drift
  hook makes the pending state visible.
- A `/config` toggle of a repo-managed key is reverted at the next sync (a
  printed diff line, not silent); per-machine overrides of managed keys are
  deliberately unsupported — override per project, or change the repo.
- `settings.personal.json.example` and all `~/.claude/settings.local.json`
  guidance are retired; the file itself is left untouched (undocumented
  Claude Code flows appear to write `autoMode`/`voice` keys there).
- A plugin entry the repo retires entirely lingers enabled in home files;
  if that ever matters, `RETIRED_KEYS` needs a per-plugin sibling.
- Re-symlinking would discard the runtime writes accumulated in the home
  file — this decision hardens over time.
