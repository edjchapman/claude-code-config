Audit project dependencies: detect the package manager, check for vulnerabilities and outdated packages, and propose an update plan.

## Arguments

`$ARGUMENTS`

- Optional: specific package to investigate, or `--security-only` to focus on vulnerabilities
- Example: `/deps`, `/deps django`, `/deps --security-only`

## Steps

### 1. Detect Package Manager

Check for these files in order:
- `pyproject.toml` / `requirements.txt` / `Pipfile` → Python (pip/uv/poetry)
- `package.json` → Node.js (npm/yarn/pnpm)
- `go.mod` → Go
- `Cargo.toml` → Rust
- `Gemfile` → Ruby

### 2. Security Audit

Run the appropriate security audit command:

| Manager | Command |
|---------|---------|
| npm | `npm audit` |
| yarn | `yarn audit` |
| pip | `pip-audit` (if available) or `safety check` |
| uv | `uv pip audit` (if available) |
| go | `govulncheck ./...` (if available) |

Report:
- Critical/high vulnerabilities with affected packages
- Whether fixes are available
- Recommended remediation steps

### 3. Check Outdated Packages

Run the appropriate command:

| Manager | Command |
|---------|---------|
| npm | `npm outdated` |
| yarn | `yarn outdated` |
| pip | `pip list --outdated` |
| uv | `uv pip list --outdated` |
| go | `go list -u -m all` |

### 4. Propose Update Plan

Categorize updates into:

**Safe updates** (patch versions, no breaking changes):
- List packages that can be updated immediately
- Provide the command to update them

**Minor updates** (new features, unlikely breaking):
- List packages with minor version bumps
- Note any with known migration steps

**Major updates** (breaking changes, require migration):
- List packages with major version bumps
- Link to changelogs/migration guides where possible
- Suggest tackling these in separate PRs

### 5. License Check (if requested)

For Node.js: `npx license-checker --summary`
For Python: `pip-licenses --summary` (if available)

## Output

Present a summary table:

```
Dependencies Summary
====================
Total packages:    XX
Outdated:          XX (safe: X, minor: X, major: X)
Vulnerabilities:   XX (critical: X, high: X, medium: X, low: X)

Recommended actions:
1. [immediate] Update safe patches: <command>
2. [this sprint] Address critical vulnerabilities
3. [planned] Major version upgrades (separate PRs)
```
