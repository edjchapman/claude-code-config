# CONTEXT.md — Domain glossary

Ubiquitous language for this repo. Skills and agents should use these terms exactly
(see `docs/agents/domain.md` for how this file is consumed).

## Terms

- **Primitive** — a unit this repo ships for Claude Code: an agent, skill, hook, rule,
  template, or CLI script. The unit the catalogs enumerate and the generator renders.
- **Catalog** — any human-facing enumeration of primitives (the README tables,
  the reference listings in `docs/architecture.md`).
- **Install modes** — the two ways this repo is consumed: **plugin mode** (via the
  plugin marketplace, reads `hooks/hooks.json`) and **global mode** (via
  `setup-global.sh`: symlinks the primitive directories into `~/.claude/`, mirrors
  `settings.json` — ADR-0002). Every hook must reach both. _Formerly
  "symlink-global mode", renamed when the settings mirror made the old name
  half-false._
- **Generated region** — a marker-fenced span of a committed file whose content is
  owned by the generator. Hand edits inside a generated region are reverted by
  regeneration; the fix belongs in the region's source.
- **Generator target** — one named unit of generation in the generator module
  (e.g. the hooks splice into `settings.json`, a catalog table): reads sources,
  produces one or more generated regions. `--only TARGET` selects one.
- **Managed key** — a `settings.json` top-level key the repo owns: the sync mirrors
  it from the repo into `~/.claude/settings.json`, overwriting any local edit
  (ADR-0002). Every other key in the home file is **unmanaged** (personal) and is
  never touched. Canonical form is "managed key" — not "repo-managed key".
- **Drift** — the state of the mirror diverging from the repo: a managed key in
  `~/.claude/settings.json` whose value no longer matches the repo's, whether from
  a runtime write or a repo edit not yet synced. Detected (warn-only) at session
  start; resolved by running the sync.
- **Scheduling invariant** — the rule that skills invoked by the cloud routines
  (daily standup #51, end-of-week review #52) must remain model-invocable, while
  user-only skills must carry `disable-model-invocation`. Enforced by the
  generator's `--check`.
