Analyze test coverage and identify gaps.

## Arguments

`$ARGUMENTS`

- `--run`: Run tests with coverage before analyzing (otherwise analyze existing coverage data)
- `--scope <path>`: Focus analysis on specific module or directory
- `--threshold <percent>`: Highlight files below this coverage threshold (default: 80)
- `--uncovered-only`: Only show files with no test coverage
- Examples: `/coverage-report`, `/coverage-report --run`, `/coverage-report --threshold 90 --scope src/api`

## Step 1: Detect Testing Framework

Check for test configuration:

```bash
ls -la pytest.ini pyproject.toml setup.cfg jest.config.* vitest.config.* 2>/dev/null
```

**Python (pytest):**

```bash
pytest --cov=. --cov-report=term-missing --cov-report=json
```

**JavaScript (Jest):**

```bash
npm test -- --coverage --coverageReporters=text --coverageReporters=json
```

**JavaScript (Vitest):**

```bash
npx vitest run --coverage
```

## Step 2: Invoke Test Engineer Agent

Launch the test-engineer agent to analyze coverage gaps:

```
Task(subagent_type="test-engineer", prompt="""
Analyze test coverage and identify gaps:

Coverage data location: {coverage_file}
Focus scope: {scope or "entire codebase"}
Minimum threshold: {threshold}%

For each file/module below threshold:
1. Identify untested functions and methods
2. Prioritize by risk (critical paths, error handling, security)
3. Suggest specific test cases to add
4. Estimate effort to reach threshold

Focus on meaningful coverage, not just line count.
""")
```

## Step 3: Parse Coverage Data

Extract key metrics:

- Overall coverage percentage
- Files below threshold
- Uncovered lines by file
- Branch coverage (if available)

## Step 4: Analyze Critical Gaps

Prioritize coverage gaps by:

1. **Security-critical code**: Authentication, authorization, input validation
2. **Business-critical code**: Core business logic, payment processing
3. **Error handling**: Catch blocks, error paths
4. **Edge cases**: Boundary conditions, null handling

## Output Format

### Test Coverage Report

**Overall Coverage:** X% (target: {threshold}%)

**Summary:**
| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Line Coverage | 75% | 80% | Below Target |
| Branch Coverage | 68% | 70% | Below Target |
| Files Covered | 45/50 | 50/50 | 5 Uncovered |

### Files Below Threshold

| File | Coverage | Gap | Priority | Suggested Tests |
|------|----------|-----|----------|-----------------|
| `src/auth/login.py` | 45% | -35% | HIGH | Auth flows, error cases |
| `src/api/orders.py` | 72% | -8% | MEDIUM | Edge cases |

### Uncovered Critical Paths

**High Priority (Security/Business Critical):**

1. `src/auth/login.py:45-67` - Password validation logic
   - **Risk**: Security-critical, no edge case testing
   - **Suggested tests**:
     - Test invalid password formats
     - Test rate limiting
     - Test lockout mechanism

2. `src/payments/process.py:89-120` - Payment processing
   - **Risk**: Business-critical, error paths untested
   - **Suggested tests**:
     - Test payment failure scenarios
     - Test timeout handling
     - Test refund flow

### Coverage Trends

If historical data available:

```
Last 5 runs:
  v1.0.0: 72% → v1.1.0: 74% → v1.2.0: 73% → v1.3.0: 75% → Current: 75%
```

### Recommendations

**Quick Wins (High impact, low effort):**

1. Add tests for `function_name` in `file.py` (+5% coverage)

**Priority Tests to Add:**

1. [Test description] - covers [functionality] - estimated effort: [S/M/L]

### Next Steps

1. Run `/lint --python-only` to check for untested code paths
2. Use test-engineer agent to generate test stubs
3. Target {threshold}% coverage before next release

## Guidelines

- Focus on meaningful coverage, not just hitting a percentage
- Prioritize testing critical paths over trivial getters/setters
- Consider mutation testing for high-confidence areas
- Coverage is a metric, not a goal - 100% coverage doesn't mean bug-free code
- Track coverage trends over time, not just point-in-time snapshots
