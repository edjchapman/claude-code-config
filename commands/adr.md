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

### 2. Gather Context

Ask the user (if not clear from arguments):
- What is the decision being made?
- What alternatives were considered?
- What are the constraints or requirements driving this decision?
- Who are the stakeholders?

### 3. Generate ADR

Create `docs/adr/NNNN-<title-slug>.md` using the Nygard format:

```markdown
# NNNN. <Title>

Date: YYYY-MM-DD

## Status

Proposed

## Context

<What is the issue or problem that motivates this decision?>
<What forces are at play (technical, business, team, etc.)?>

## Decision

<What is the decision that was made?>
<State it clearly in active voice: "We will...">

## Consequences

### Positive
- <Benefits of this decision>

### Negative
- <Trade-offs and costs>

### Neutral
- <Other effects that are neither positive nor negative>
```

### 4. Cross-Reference

- Check if this supersedes any existing ADR
- If so, update the old ADR's status to "Superseded by NNNN"
- Link related ADRs in the Context section

## Output

- Show the created ADR file path
- Present the content for review
- Ask if the user wants to modify anything before committing
- Suggest updating the ADR index if one exists (`docs/adr/README.md`)
