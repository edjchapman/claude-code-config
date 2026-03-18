Define the scope and boundaries for the current task before starting work.

> **Purpose**: Front-load constraints to prevent scope creep and wrong-approach friction. Run this at the start of a session to establish clear boundaries.

## Arguments

`$ARGUMENTS`

- If provided, use as context to pre-populate the scope definition
- Examples: `/scope Fix NaN bug in cashflow/occupancy/`, `/scope Refactor metric aggregation`, `/scope`

## Steps

### Step 1: Gather Context

If arguments were provided, use them to understand the task. Otherwise, ask the user:

> What is the primary task for this session?

### Step 2: Define Scope

Work with the user to establish these five boundaries. Present them as a checklist and confirm each:

1. **Primary objective** — What is the one main deliverable?
2. **Files in scope** — Which files or directories should be modified?
3. **Files out of scope** — Which files must NOT be touched?
4. **Approach** — Key constraints on how to implement:
   - Fix root cause or patch symptom?
   - Derive from existing config or create new?
   - Refactor or minimal change?
5. **Success criteria** — How do we know this session succeeded?
   - Tests passing?
   - PR created?
   - Plan document written?

### Step 3: Confirm and Lock

Present the scope definition as a compact summary:

```
Scope: [task name]
────────────────────────────────
Objective:  [one sentence]
In scope:   [files/dirs]
Out of scope: [files/dirs]
Approach:   [key constraints]
Done when:  [success criteria]
────────────────────────────────
```

Ask the user to confirm before proceeding with any work.

## Guidelines

- Keep scope as narrow as possible — one task per session produces better outcomes
- If the user's request implies multiple tasks, suggest splitting into separate sessions
- Reference this scope definition if work starts drifting beyond boundaries
- If new scope is needed mid-session, re-run `/scope` to redefine boundaries
