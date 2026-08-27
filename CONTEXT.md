# CONTEXT.md — Domain glossary

Ubiquitous language for this repo. Skills and agents should use these terms exactly
(see `docs/agents/domain.md` for how this file is consumed).

## Terms

- **Primitive** — a unit this repo ships for Claude Code: an agent, skill, hook, rule,
  template, or CLI script. The unit the catalogs enumerate and the generator renders.
- **Rule** — the primitive that carries _judgement a linter cannot express_, loaded
  as **context** when Claude reads a file matching its `paths` frontmatter. Rules
  **inform; they never enforce** — enforcement is a hook or a linter, and content a
  linter already flags or autofixes does not belong in one. Delivered at user level
  (`~/.claude/rules/`, global mode only), so a rule applies to _every_ repo of that
  language on the machine: nothing in one may assume a particular linter config,
  framework, or language version. Framework guidance is a **skill** instead
  (`django-patterns`, `docker-patterns`) — language → rule, framework → skill.
  _Formerly described as "style enforcement", which invited linter content into
  rules and is why the retired bullets sat unexamined._
- **Catalog** — any human-facing enumeration of primitives (the README tables,
  the reference listings in `docs/architecture.md`).
- **Install modes** — the two ways this repo is consumed: **plugin mode** (via the
  plugin marketplace, reads `hooks/hooks.json`) and **global mode** (via
  `setup-global.sh`: symlinks the primitive directories into `~/.claude/`, mirrors
  `settings.json` — ADR-0002). Every hook must reach both. Concerns how Claude Code
  loads this repo's primitives — a different axis from the **layers** a target
  project receives, despite both being called "install". _Formerly
  "symlink-global mode", renamed when the settings mirror made the old name
  half-false._
- **Claude layer** — what a target project receives **by reference**: the primitives
  reach it via symlink or generation, so a change here propagates to every project
  without re-running anything.
- **Tooling layer** — what a target project receives **by copy**: the quality gate,
  validators, git hooks, and CI become that repo's own source. Nothing propagates —
  picking up a change means re-running the install. This asymmetry with the Claude
  layer is what makes "did my fix reach that project?" answerable.
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
- **Trigger collision** — two primitives whose descriptions claim the same invocation
  situation, making which one fires nondeterministic. Applies **across primitive types**
  (a skill and an agent compete for the same dispatch decision), not only skill-to-skill.
  Resolved by **retirement** (delete the weaker one) or **delegation** (narrow one
  primitive's trigger and have its body invoke the other as the method).
- **Canonical primitive** — the single primitive that owns a given trigger after a
  collision is resolved. Every trigger has at most one.
- **Third-party primitive** — a primitive this repo _enables_ but does not _own_: a skill
  or agent shipped by an external plugin (currently `mattpocock-skills`). It costs
  always-loaded context like any other primitive, but cannot be edited — a trigger
  collision with one is resolved by demoting it (`skillOverrides`) or by narrowing
  our own primitive, never by editing theirs. Its version is a **pin**; its shipped
  set is captured in a committed **lockfile** so upstream change surfaces as a diff.
- **Scheduling invariant** — the rule that skills invoked by the cloud routines
  (daily standup #51, end-of-week review #52) must remain model-invocable, while
  user-only skills must carry `disable-model-invocation`. Enforced by the
  generator's `--check`.
