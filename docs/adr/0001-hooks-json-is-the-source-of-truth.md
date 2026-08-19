# ADR-0001: `hooks/hooks.json` is the source of truth for hook definitions

**Status:** Accepted — 2026-08-19

## Context

Every hook was defined identically in two committed files: `settings.json`'s `hooks`
key (read in symlink-global mode) and `hooks/hooks.json` (read in plugin mode) —
94 lines duplicated verbatim, held equal by `check-hooks-sync.py`. The checker
policed the copied part but was blind to adjacent gaps (e.g. `statusLine` exists
only in `settings.json`; verified against the plugin docs, plugins cannot provide
a statusLine at all, so that gap is a platform limitation, not drift).

Both files must remain committed: each install mode consumes its file directly,
so neither can be produced at install time only.

## Decision

- `hooks/hooks.json` is the single source of truth for hook definitions. It is the
  purpose-shaped module (hooks and nothing else) and matches the external contract
  of the plugin loader.
- `settings.json`'s `hooks` key is a **generated region**, produced by the repo's
  generator module (`scripts/generate.py`), which preserves every other key of
  `settings.json` untouched.
- Pre-commit regenerates (repo convention: hooks may mutate commits, as the
  formatters already do); CI runs `generate.py --check` as the backstop.
  `check-hooks-sync.py` is deleted.

## Consequences

- Hooks are edited in exactly one place. Hand edits to the generated block in
  `settings.json` are silently reverted at commit time — by design.
- In symlink-global mode a `hooks.json` edit takes effect in the live config only
  after regeneration (pre-commit, or running the generator manually).
- The generator gives future work (catalog generation, and a possible rendered
  install per the architecture review's candidate D) a canonical, hooks-only input.
- `statusLine` remains a settings-only key; plugin mode cannot carry one.
