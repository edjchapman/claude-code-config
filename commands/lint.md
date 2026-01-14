Run all linters for the current project and summarize results.

## Steps

1. **Detect project type** by checking for config files:
   ```bash
   ls -la pyproject.toml setup.py setup.cfg requirements.txt package.json tsconfig.json 2>/dev/null
   ```

2. **For Python projects** (pyproject.toml, setup.py, or requirements.txt):
   - Check for pre-commit: `ls .pre-commit-config.yaml 2>/dev/null`
   - If pre-commit exists: `pre-commit run --all-files`
   - Otherwise run individual linters:
     - `ruff check .` or `flake8` (check which is configured)
     - `ruff format --check .` or `black --check .`
     - `isort --check .`
     - `mypy .` (if configured)

3. **For JavaScript/TypeScript projects** (package.json):
   - Check package.json scripts for lint commands
   - Common patterns:
     - `npm run lint` or `yarn lint` or `pnpm lint`
     - `npx eslint .`
     - `npx prettier --check .`
     - `npx tsc --noEmit` (type checking)

4. **For mixed projects**:
   - Run both Python and JS/TS linters

## Output Format

### Lint Results

**Project Type**: [Python/JavaScript/TypeScript/Mixed]

**Commands Run**:
- `command 1` - [PASS/FAIL]
- `command 2` - [PASS/FAIL]

### Issues Found

[Group by severity if possible]

#### Errors (must fix)
- file:line - description

#### Warnings (should fix)
- file:line - description

### Summary
- Total files checked: N
- Errors: N
- Warnings: N
- Status: [CLEAN / NEEDS FIXES]

If there are many issues, group them by file or by error type rather than listing every single one.