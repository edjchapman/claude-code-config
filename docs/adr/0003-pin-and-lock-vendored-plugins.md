# ADR-0003: Third-party plugin primitives are pinned and locked

**Status:** Accepted — 2026-08-24, revised 2026-09-09 (the pin is a tag, not a SHA)

## Context

`settings.json` enables one plugin this repo does not own —
`mattpocock-skills@mattpocock`, via an `extraKnownMarketplaces` entry pointing at
`github:mattpocock/skills`. Its skills are **third-party primitives**: they cost
always-loaded context exactly like the skills and agents this repo ships, they
compete with them for the same dispatch decisions, and they cannot be edited here.

Three problems followed from enabling it without any declared invariant.

**The marketplace entry carried no `ref`, so it tracked the upstream default
branch.** In practice that produced neither reproducibility nor freshness: the
installed cache sat at commit `2ab9580` from 2026-07-31 — an untagged `main`
commit — while upstream had moved on through `v1.2.3`. "Unpinned" did not mean
"latest"; it meant _whatever was fetched last, unknowably_.

**Upstream controls which skills reach a session, and the blast radius is
invisible from here.** The plugin's `.claude-plugin/plugin.json` whitelists a
subset of the skills in its repository — 22 of 41 at the pinned commit. Adding one
line there puts a new model-invocable description into every session. This is not
hypothetical: between the pinned commit and `v1.2.3` the whitelist gains `wizard`
and `writing-for-agents`, the latter triggering on _"creating or editing skills, or
modifying AGENTS.md or CLAUDE.md"_ — which is precisely what this repository is
for, and would collide with `docs/extending.md`'s own Self-Extension Guide.
_(Revised 2026-09-09: it competes with a document, not a dispatchable primitive,
so it is additive rather than a collision — see `docs/extending.md`.)_

**Revised 2026-09-09 — the SHA pin was not installable from scratch.** Claude
Code 2.1.266 introduced a marketplace reconciler that (a) ignores any marketplace
whose entry in `~/.claude/plugins/known_marketplaces.json` differs from its
`extraKnownMarketplaces` declaration, `ref` included, and (b) heals the gap by
re-cloning with `git clone --branch <ref>`, which git only accepts for a branch
or tag name. The SHA below had been declared after the marketplace was
registered, so the registry never carried it; older versions tolerated the
drift, 2.1.266 dropped the plugin from every session, and the auto-heal failed
with `Remote branch 2ab958… not found in upstream origin`. The pin had been
verified against the refresh path only; a fresh clone was never tried
([#152](https://github.com/edjchapman/claude-code-config/issues/152)).

**The context budget was measuring the wrong surface.** `check-context-budget.py`
counted only `tracked_files(...)` — this repo's own primitives — reporting 5,805 B
against a 10,240 B budget while the true always-loaded cost was 7,649 B. The
enabled plugin contributed 1,844 B that CI could not see, including a single
419 B description exceeding the repo's own 350 B per-item warning threshold.

The obstacle to enforcement is that the plugin's source lives in
`~/.claude/plugins/cache/`, a machine-local artifact that does not exist in CI.
Any check reading it live is blind on GitHub Actions.

## Decision

**Pin the marketplace by `ref`.** `extraKnownMarketplaces` gains
`"ref": "2ab958093e83e0ec752e6c1c5932da465bf23e0c"` _(since 2026-09-09: `"v1.2.3"`)_. The field is honoured by
Claude Code's marketplace refresh (`git fetch origin <ref>` → `checkout` →
`pull origin <ref>`), verified end-to-end against the upstream repository before
adoption.

_Superseded 2026-09-09 — see the rule below._ The pin is a **commit SHA, not a
tag**, against the general preference for readable refs. No tag reproduces the reviewed state: `v1.2.0` (`e903586`),
`v1.2.2`, and `v1.2.3` all ship the wider 25-skill whitelist, so pinning to any
tag would be a content change (+2 model-invocable skills, +417 B) disguised as a
reproducibility fix. The SHA pins what has actually been in use and reviewed
since July. Moving to `v1.2.3` is a real decision with a known cost, deliberately
left for a separate, reviewed commit.

**Revised 2026-09-09 — the ref is a tag, and must be a branch or tag name.**
The pin is `v1.2.3`; `generate.py --check` rejects a SHA-shaped ref. The content
cost deferred above — `wizard` and `writing-for-agents` become model-invocable —
is accepted, with the always-loaded budget raised in the same change. The
lockfile diff was read as the review: `wizard` was checked against the
provisioning and migration primitives and found to be a different situation,
not a competing method (`docs/extending.md` records both verdicts).

**Commit a lockfile.** `plugins/mattpocock-skills.lock.json` records the pinned
ref, the plugin version, every skill the pin ships, each description verbatim,
and whether each is model-invocable. It is generated from the local cache by
`scripts/update-plugin-lock.py` and is never regenerated in CI — CI verifies it.

**Enforce both, in the idiom the repo already uses for declared invariants.**
`scripts/lib/vendored_plugins.py` is the single source both consumers derive from:

- `generate.py --check` fails when `settings.json`'s pin and the lockfile
  disagree in either direction — a moved pin with a stale lockfile means an
  unreviewed plugin reaches every session; a regenerated lockfile with an unmoved
  pin means the review happened against something this config never loads.
- `check-context-budget.py` counts the lockfile's model-invocable descriptions
  into the budget, and tells a breaching third-party primitive to be demoted or
  dropped rather than "trimmed" — advice that cannot apply to a file this repo
  does not own.

Alternatives rejected: a live check against the plugin cache (silently no-ops in
CI, which is where enforcement matters); budget accounting alone (catches cost
growth but not the trigger changes that cause collisions); and staying unpinned
(no mechanism can detect drift from an undefined baseline).

## Consequences

Upgrading the plugin is now a deliberate three-step act — move the pin,
regenerate the lockfile, read the diff — and the lockfile diff is the review:
every changed description is a collision candidate against this repo's own
primitives. Forgetting a step fails `generate.py --check`, which pre-commit and
CI both run.

The reported context budget rose from 5,805 B to 7,649 B without a single byte
being added. That number is not a regression; it is the first honest measurement,
and it consumes 75% of the budget rather than the 57% previously believed.
Vendoring a second plugin would very likely require raising the budget or
demoting something.

The repo now carries a generated artifact that **cannot be regenerated in CI**,
which is a new category here — every other generated region is derivable from
committed sources. The lockfile is therefore reviewed as input, not verified as
output. A hand-edited lockfile would pass every check; the mitigation is that
editing it is pointless, since it changes nothing about what loads.

Pinning to a SHA _(since 2026-09-09: a tag)_ freezes this config at a state upstream
has moved past. That is
the intended trade — but it means missing upstream fixes until someone chooses to
bump, and nothing here schedules or prompts that choice.

A tag pin gives up what the SHA gave: upstream can move `v1.2.3` and every check
here still passes, because the lockfile records the ref, not the commit it
resolved to. Recording that commit is a follow-up, not part of this revision.
