---
name: adr
description: Record a technical decision as an Architecture Decision Record. Use when weighing a framework, library, database, or schema-migration trade-off, or when asked for an ADR.
argument-hint: "<decision summary>"
---

Create an Architecture Decision Record (ADR) documenting a technical decision.

## Arguments

`$ARGUMENTS`

- Describe the decision to document
- Example: `/adr switch from REST to GraphQL for mobile API`
- Example: `/adr use PostgreSQL for event sourcing`

## Steps

### 1. Determine ADR Number

Check for existing ADRs:

```bash
ls docs/adr/ 2>/dev/null || echo "No ADR directory yet"
```

If the directory doesn't exist, create it:

```bash
mkdir -p docs/adr
```

Determine the next number by counting existing ADRs, starting from `0001`.

### 2. Check the decision is ADR-worthy

Read `docs/adr/README.md` if the target repo has one — it is the destination's own
spec and **outranks anything in this skill**. More than one primitive can write to
`docs/adr/` (this skill, `@documentation-writer`, the vendored
`mattpocock-skills:domain-modeling`), so the format lives beside the ADRs rather
than in any one producer.

If there is no `docs/adr/README.md`, apply this bar. All three must be true:

1. **Hard to reverse** — changing your mind later carries a meaningful cost.
2. **Surprising without context** — a future reader will wonder "why this way?"
3. **The result of a real trade-off** — genuine alternatives existed.

If any is missing, say so and stop. A convention or a workflow step is documentation,
not an ADR.

### 3. Gather context

Ask the user (if not clear from arguments):

- What is the decision being made?
- What alternatives were considered, and why were they rejected?
- What constraints or requirements forced it?
- What does it cost — an ADR that lists only benefits is an advertisement.

### 4. Write the ADR

Create `docs/adr/NNNN-<title-slug>.md`. Follow `docs/adr/README.md` where it exists.
Otherwise use this shape — the title is a **claim**, not a topic:

```markdown
# ADR-NNNN: <Decision stated as a claim>

**Status:** Accepted — YYYY-MM-DD

## Context

<What forced the decision: constraints in play, and what was already true.>

## Decision

<What was decided, in active voice. Name rejected alternatives and why.>

## Consequences

<What follows — including the costs and anything now harder.>
```

### 5. Cross-reference

- Check if this supersedes any existing ADR
- If so, update the old ADR's status to "Superseded by NNNN"
- Link related ADRs in the Context section

## Output

- Show the created ADR file path
- Present the content for review
- Ask if the user wants to modify anything before committing
- Suggest updating the ADR index if one exists (`docs/adr/README.md`)
