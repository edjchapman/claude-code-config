Audit project dependencies for vulnerabilities, outdated packages, and license issues.

> **Quick entry point** for dependency management. Delegates to `@dependency-manager` agent for comprehensive analysis.

## Arguments

`$ARGUMENTS`

- Optional: specific package to investigate, or flags for focused analysis
- Example: `/deps`, `/deps django`, `/deps --security-only`

## Behavior

This command invokes the `@dependency-manager` agent, which handles:

- **Package manager detection**: pip/uv/poetry, npm/yarn/pnpm, go modules, cargo, etc.
- **Security audit**: CVE scanning, vulnerability severity, remediation steps
- **Outdated analysis**: Safe patches, minor updates, major upgrades
- **License checks**: Compatibility analysis when requested
- **Upgrade planning**: Categorized by risk level with commands to execute

## When to Use

| Scenario | Command |
|----------|---------|
| Quick audit before release | `/deps` |
| Investigate specific package | `/deps requests` |
| Security-focused check | `/deps --security-only` |
| Pre-upgrade assessment | `/deps --major-updates` |

## Delegation

Invoke `@dependency-manager` with the user's arguments:

```
@dependency-manager $ARGUMENTS
```

The agent will:
1. Detect the project's package manager(s)
2. Run appropriate audit commands
3. Analyze and categorize findings
4. Present an actionable summary with prioritized recommendations
