# CONTEXT.md — Domain glossary

Ubiquitous language for this repo. Skills and agents should use these terms exactly
(see `docs/agents/domain.md` for how this file is consumed).

## Terms

- **Primitive** — a unit this repo ships for Claude Code: an agent, skill, hook, rule,
  template, output style, or CLI script. The unit the catalogs enumerate and the
  generator renders.
- **Output style** — the primitive that owns Claude's conversational response format,
  activated by the `outputStyle` managed key. Comes in two modes: **augmenting**
  (keeps the harness's own instructions and layers extra guidance on top, so harness
  improvements keep flowing) and **replacing** (discards them). This repo's style is
  augmenting — replacing would freeze out upstream output improvements. The mode is
  `keep-coding-instructions`, which only bites on the _full_ system prompt; newer
  models get the shorter prompt, which has no coding section to keep or discard.
- **Scannable** — this repo's output style: full detail, never prose walls, plainly
  worded. Substantial answers lead with the outcome, then anchored bullets for parallel
  items, a short paragraph for a chain of reasoning, tables for enumerable facts;
  brief educational insights stay inside their own box. A **working turn** is answered
  with a **turn report**, and whatever waits on the reader — a **fork**'s options, a
  clarifying question — comes last. **Threshold-based** — one-fact answers stay a plain
  sentence; the structure is mandatory only once an answer carries more than a couple
  of sentences or facts. Over-formatting a trivial reply is the mirror-image failure
  of a prose wall.
- **Working turn** — a turn whose work cannot be told in a couple of sentences: an
  investigation across several files or commands, or a change that touches more than
  one place. An investigation that edits nothing can be a working turn; a lookup or a
  small routine change is not one, whatever tools it used.
- **Turn report** — the form a working turn's reply takes: what was found, what changed,
  what was verified, what is unresolved. It _is_ the reply's body, not a recap appended
  to it. _Verified_ and _unresolved_ are always stated, even when the answer is
  "nothing", so silence never has to be interpreted. Scoped to that turn alone. Not a
  **session recap** (a cumulative account of the whole conversation), which Scannable
  does not produce.
- **Fork** — a point where the next move is a decision that belongs to the user, not to
  Claude. The only occasion on which a reply offers **next-step options**; work already
  inside what was asked is never a fork and is never offered as an option.
- **Rule** — the primitive that carries _judgement a linter cannot express_, loaded
  as **context** when Claude reads a file matching its `paths` frontmatter. Rules
  **inform; they never enforce** — enforcement is a hook or a linter, and content a
  linter already flags or autofixes does not belong in one. Delivered at user level
  (`~/.claude/rules/`, global mode only), so a rule applies to _every_ repo of that
  language on the machine: nothing in one may assume a particular linter config,
  framework, or language version. Framework guidance is a **skill** instead
  (`ccc-django-patterns`, `ccc-docker-patterns`) — language → rule, framework → skill.
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
  always-loaded context like any other primitive, but cannot be edited or demoted
  (`skillOverrides` is inert for plugin-sourced skills, #159) — a trigger collision
  with one is resolved by narrowing our own primitive or dropping the pin, never by
  editing theirs; an over-guideline description is accepted at a recorded size. Its version is a **pin**; its shipped
  set is captured in a committed **lockfile** so upstream change surfaces as a diff.
- **Scheduling invariant** — the rule that skills invoked by the cloud routines
  (daily standup #51, upstream watch #187) must remain model-invocable, while
  user-only skills must carry `disable-model-invocation`. Enforced by the
  generator's `--check`.
- **Wired-coverage invariant** — the rule that every tracked script under
  `scripts/hooks/` is fired by a binding in `hooks/hooks.json`, or is declared
  a non-hook (`NON_HOOK_SCRIPTS`) with what runs it instead. Restores what the
  retired mention-grep checker caught: a script added and never wired. Enforced
  by the generator's `--check`, like the scheduling invariant.
- **No-count rule** — hand-written prose in a catalog-bearing doc states no count
  of primitives, cloud routines, or enabled plugins; every count is a generated
  region. Asserted by the generator's `--check` over the hand-written spans and
  scoped to those declared sets, so an architectural count ("two install modes")
  is not a violation.
- **Usage review** — the examination of a user's own Claude Code session history
  for places where their config costs output quality or efficiency. Shipped to every
  consumer, so "their config" is whatever that user runs, not only this repo. Its
  evidence exists only on the machine the sessions ran on, and only **aggregates**
  of it (counts, totals, tool, hook and model names) may be published — never a
  prompt, file path, or project name. One of the two ways the
  config improves itself; not to be merged with **upstream watch**, which looks
  outward rather than at usage.
- **Upstream watch** — the examination of Claude Code's released changes for what
  this config should adopt and what they have made stale. Needs nothing from the
  maintainer's machine, and is the maintainer's alone — not shipped to consumers.
  Its findings rank by kind: **breakage** (a release broke something relied on),
  **deprecation** (still works, marked legacy), **refresh** (a declared set no
  longer matches the platform), then **adoption** (a new capability, optional).
- **Opted-in repo** — a repo that has declared a usage review may open pull requests
  against it, and on which sessions the review's evidence rests (that repo's, or
  every project's when its config is global). Everywhere else a usage review is
  **report-only**: it publishes nothing.
- **Proposal** — the shared output unit of a usage review or an upstream watch: one
  suggested change to a config, ranked against the others and carrying the
  evidence for it. The best few of a run become pull requests, one change each;
  the repo's owner merges or closes them — a proposal is never merged by the loop
  that made it, and closing one is a **rejection** that stands unless its signal
  worsens. One from a usage review names the **signal** it expects to move,
  so a later review can judge whether the change worked.
- **Verdict** — a later usage review's judgement of a merged proposal against the
  signal it named: **improved**, **no change**, **worse**, or **inconclusive** (the
  comparison was confounded, e.g. the daily model changed). Only _worse_ leads
  anywhere — to a new proposal to revert. Upstream-watch proposals get no verdict;
  they name no signal.
- **Signal** — a countable measure of session history that a usage review tracks.
  **Efficiency signals** measure cost directly (context size, compactions,
  always-loaded context, permission prompts, hook latency, failed tool calls).
  **Quality proxies** (interruptions, corrections, denied tool calls) stand in for
  output quality, which session history does not record directly.
