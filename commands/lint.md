Run all linters for the current project and summarize results.

## Arguments

`$ARGUMENTS`

- `--python-only`: Run only Python linters (ruff, black, mypy, etc.)
- `--js-only`: Run only JavaScript/TypeScript linters (eslint, prettier, tsc)
- `--fix`: Auto-fix issues where possible (ruff --fix, eslint --fix, prettier --write)
- `--staged`: Only lint staged files (useful before commit)
- Examples: `/lint --python-only --fix`, `/lint --js-only`, `/lint --staged`

## Steps

1. **Detect project type** by checking for config files:
   ```bash
   ls -la pyproject.toml setup.py setup.cfg requirements.txt package.json tsconfig.json .eslintrc* .prettierrc* ruff.toml 2>/dev/null
   ```

   **Auto-detection priority:**
   - `pyproject.toml` with `[tool.ruff]` → use ruff
   - `pyproject.toml` with `[tool.black]` → use black
   - `.flake8` or `setup.cfg` with flake8 config → use flake8
   - `.eslintrc*` or `eslint.config.*` → use eslint
   - `.prettierrc*` → use prettier

2. **For Python projects** (skip if `--js-only`):
   - Check for pre-commit: `ls .pre-commit-config.yaml 2>/dev/null`
   - If pre-commit exists and no `--fix` flag: `pre-commit run --all-files`
   - Otherwise run individual linters:
     - **Ruff** (preferred): `ruff check .` or `ruff check --fix .` if `--fix`
     - **Format check**: `ruff format --check .` or `ruff format .` if `--fix`
     - **Fallback**: `black --check .` / `black .` if `--fix`
     - **Import sorting**: `isort --check .` / `isort .` if `--fix`
     - **Type checking**: `mypy .` (if mypy.ini or pyproject.toml has mypy config)
     - **Type checking alt**: `basedpyright .` (if pyrightconfig.json exists)

3. **For JavaScript/TypeScript projects** (skip if `--python-only`):
   - Check package.json scripts for lint commands
   - **ESLint**:
     - Check: `npx eslint .`
     - Fix: `npx eslint --fix .` if `--fix`
   - **Prettier**:
     - Check: `npx prettier --check .`
     - Fix: `npx prettier --write .` if `--fix`
   - **TypeScript**:
     - `npx tsc --noEmit` (type checking, no auto-fix)
   - **Package manager detection**: Use npm/yarn/pnpm based on lockfile

4. **For mixed projects** (neither `--python-only` nor `--js-only`):
   - Run both Python and JS/TS linters

5. **For `--staged` flag**:
   - Get staged files: `git diff --cached --name-only`
   - Filter by extension and run linters only on those files

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