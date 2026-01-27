Run a security audit on the codebase.

## Arguments

`$ARGUMENTS`

- `--scope <path>`: Limit scan to specific directory or file (default: entire codebase)
- `--type <type>`: Focus on specific security area: `deps`, `code`, `secrets`, `all` (default: all)
- `--severity <level>`: Minimum severity to report: `low`, `medium`, `high`, `critical` (default: medium)
- `--create-issues`: Create GitHub issues for critical findings
- Examples: `/security-scan`, `/security-scan --scope src/auth --type code`, `/security-scan --severity critical`

## Step 1: Invoke Security Auditor Agent

Launch the security-auditor agent to perform the comprehensive audit:

```
Task(subagent_type="security-auditor", prompt="""
Perform a security audit with the following parameters:
- Scope: {scope or "entire codebase"}
- Focus areas: {type or "all"}
- Minimum severity: {severity or "medium"}

Scan for:
1. OWASP Top 10 vulnerabilities
2. Hardcoded secrets and credentials
3. Dependency vulnerabilities
4. Insecure configurations
5. Authentication/authorization issues

Provide findings in structured format with severity, location, and remediation steps.
""")
```

## Step 2: Dependency Vulnerability Check

Run appropriate dependency scanners based on project type:

**Python:**
```bash
# If pip-audit is available
pip-audit
# or
safety check -r requirements.txt
```

**JavaScript/Node:**
```bash
npm audit
# or
yarn audit
```

**General:**
```bash
# Check for known CVEs in dependencies
```

## Step 3: Secret Detection

Scan for exposed secrets:

**Patterns to check:**
- API keys and tokens
- Database credentials
- Private keys
- AWS/GCP/Azure credentials
- OAuth secrets

```bash
# Use grep patterns or dedicated tools like gitleaks, trufflehog
```

## Step 4: Create Issues (if `--create-issues`)

**If GitHub MCP is available (`mcp__plugin_github_github__issue_write`):**
- Create issues for CRITICAL and HIGH severity findings
- Label issues as `security`, `priority:high`
- Assign to appropriate team if configured

**If GitHub MCP is NOT available:**
```bash
gh issue create --title "Security: [finding title]" --body "[details]" --label "security"
```

## Output Format

### Security Scan Report

**Scan Summary:**
- Scope: [scanned area]
- Total findings: X (Y critical, Z high, W medium, V low)
- Scan date: [timestamp]

### Critical Findings (Action Required)

For each finding:
- **[Type]** Finding Title
  - **Severity**: CRITICAL
  - **Location**: `file:line`
  - **Description**: What the issue is
  - **Impact**: What could happen
  - **Remediation**: How to fix it
  - **Issue**: [link if created]

### High Severity Findings
[Same format]

### Medium Severity Findings
[Same format, can be more concise]

### Low Severity / Informational
[Brief list]

### Dependency Vulnerabilities

| Package | Current | Fixed Version | CVE | Severity |
|---------|---------|---------------|-----|----------|
| example | 1.2.3 | 1.2.4 | CVE-2024-XXX | High |

### Next Steps

1. [Prioritized action items]
2. [Recommended timeline]

## Guidelines

- Always scan the entire dependency tree, not just direct dependencies
- Check both code AND configuration files (Dockerfiles, CI configs, etc.)
- Consider the threat model - what data is the application handling?
- Prioritize findings by actual exploitability, not just theoretical severity
- Provide clear, actionable remediation steps for each finding
