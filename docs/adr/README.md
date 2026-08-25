# Architecture Decision Records

The house format and the bar for writing one. This file lives **beside the ADRs
rather than inside the skill that writes them** on purpose: more than one
primitive can create a file here — this repo's `/adr` skill, `@documentation-writer`,
and the vendored `mattpocock-skills:domain-modeling` — and only some of them are
ours to edit. A convention enforced in each producer is unenforceable once a
producer is vendored; a convention published at the destination is read by
whichever one fires.

**Writing an ADR here?** Follow this file, not your own template.

## Should this be an ADR?

All three must be true. If any is missing, skip it — the record costs more than
it returns.

1. **Hard to reverse** — the cost of changing your mind later is meaningful.
2. **Surprising without context** — a future reader will look at the result and
   wonder "why on earth did they do it this way?"
3. **The result of a real trade-off** — there were genuine alternatives, and one
   was picked for specific reasons.

Easy to reverse? You will just reverse it. Not surprising? Nobody will wonder.
No real alternative? There is nothing to record beyond "we did the obvious thing."

Conventions that are merely _documented_ — a naming rule, a lint policy, a
workflow step — belong in `docs/extending.md` or the relevant skill, not here.

## Format

One file per decision: `docs/adr/NNNN-kebab-slug.md`, numbered sequentially from
the highest existing number.

```markdown
# ADR-NNNN: <Decision stated as a claim, not a topic>

**Status:** Accepted — YYYY-MM-DD

## Context

What forced the decision. The constraints in play, and what was already true
before it — enough that a reader who was not there can reconstruct the problem.

## Decision

What was decided, in active voice ("`hooks/hooks.json` is the source of truth…").
State the alternatives that were rejected and why, where the rejection is not
self-evident.

## Consequences

What follows — including the costs. An ADR that lists only benefits is a
advertisement, not a record.
```

Notes on the shape, all visible in `0001` and `0002`:

- The title is a **claim**, not a subject line: "Mirror `settings.json` instead of
  symlinking it", not "Settings file handling".
- **Status** is a bold line under the title with the date the decision was taken —
  not a `## Status` section. Use `Accepted`, `Superseded by ADR-NNNN`, or
  `Deprecated`.
- Three sections, always: Context, Decision, Consequences. No `Date:` line, no
  positive/negative/neutral subheadings.
- Prose wrapped at roughly 90 columns, matching the rest of `docs/`.

## Superseding

When a new ADR replaces an old one, edit the old file's status line to
`**Status:** Superseded by ADR-NNNN — YYYY-MM-DD` and link the new record from
its Context. Never delete an ADR: the record of a decision that was later
reversed is more valuable than its absence.
