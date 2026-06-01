# Security Policy

This is a personal configuration repository — it contains no production code, no credentials, and no network-facing surface of its own. The realistic security surface is:

- Hook scripts in `scripts/hooks/` execute on every Claude Code session
- `settings-templates/` and `mcp-templates/` JSON files get merged into `settings.local.json` / `.mcp.json` for downstream projects

If you find a vulnerability, **please do not open a public issue.**

## Reporting a vulnerability

- **Preferred:** Use [GitHub's private security advisory](https://github.com/edjchapman/claude-code-config/security/advisories/new) to report directly to the maintainer.
- **Fallback:** Email `edchapman88@gmail.com` with the word `SECURITY` in the subject line.

Please include:

- A description of the issue and the impact (what an attacker could do)
- Steps to reproduce, or a minimal proof-of-concept
- Your assessment of severity if you have one

I'll acknowledge receipt within 7 days and aim to ship a fix or mitigation within 30 days for high-severity issues. Lower-severity findings may take longer.

## Out of scope

- Issues in upstream Claude Code, Anthropic plugins, or third-party MCP servers — please report those to their respective maintainers.
- Findings that require the attacker to already have write access to this repo (since at that point the repo trust model has already broken).
