Guide me through a TDD (Test-Driven Development) workflow for the given feature or change.

## Arguments

`$ARGUMENTS`

- Describe the feature, function, or change to implement using TDD
- Example: `/tdd add email validation to user registration`

## Workflow

Follow this strict Red-Green-Refactor cycle:

### Step 1: RED - Write a Failing Test

1. **Understand the requirement** from the arguments
2. **Write the simplest failing test** that describes the expected behavior
3. **Run the test** to confirm it fails:
   - Python: `pytest <test_file> -x -v`
   - TypeScript: `npx vitest run <test_file>` or `npm test -- <test_file>`
4. **Show the failure output** to confirm the test fails for the right reason

### Step 2: GREEN - Write Minimal Implementation

1. Write the **minimum code** needed to make the failing test pass
2. Do NOT add extra logic, edge cases, or optimizations yet
3. **Run the test** again to confirm it passes
4. **Show the passing output**

### Step 3: REFACTOR - Clean Up

1. Review both the test and implementation for:
   - Duplication
   - Naming clarity
   - Unnecessary complexity
2. Refactor if needed while keeping tests green
3. **Run all related tests** to confirm nothing broke

### Step 4: Next Cycle

1. Ask: "What's the next behavior to test?"
2. Suggest 2-3 natural next test cases (edge cases, error handling, etc.)
3. Wait for user confirmation before writing the next test
4. Repeat from Step 1

## Rules

- **Never write implementation before the test**
- **Never write more than one test at a time**
- **Never add code that isn't required by a failing test**
- Each cycle should be small and focused (under 20 lines of new code)
- If the user asks to skip ahead, remind them of the TDD discipline

## Output

After each cycle, show:
- Test count: total / passing / failing
- Files modified in this cycle
- Suggested next test cases
