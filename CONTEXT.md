# CONTEXT.md — Domain glossary

Ubiquitous language for this repo. Skills and agents should use these terms exactly
(see `docs/agents/domain.md` for how this file is consumed).

## Terms

- **Primitive** — a unit this repo ships for Claude Code: an agent, skill, hook, rule,
  template, or CLI script. The unit the catalogs enumerate and the generator renders.
- **Catalog** — any human-facing enumeration of primitives (the README tables,
  the reference listings in `docs/architecture.md`).
- **Install modes** — the two ways this repo is consumed: **plugin mode** (via the
  plugin marketplace, reads `hooks/hooks.json`) and **symlink-global mode**
  (via `setup-global.sh`, reads `settings.json`). Every hook must reach both.
- **Generated region** — a marker-fenced span of a committed file whose content is
  owned by the generator. Hand edits inside a generated region are reverted by
  regeneration; the fix belongs in the region's source.
- **Generator target** — one named unit of generation in the generator module
  (e.g. the hooks splice into `settings.json`, a catalog table): reads sources,
  produces one or more generated regions. `--only TARGET` selects one.
- **Scheduling invariant** — the rule that skills invoked by the cloud routines
  (daily standup #51, end-of-week review #52) must remain model-invocable, while
  user-only skills must carry `disable-model-invocation`. Enforced by the
  generator's `--check`.
