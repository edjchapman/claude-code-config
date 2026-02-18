# MCP Servers Configuration

This document explains how MCP (Model Context Protocol) servers are configured and used within this Claude Code configuration repository.

## Overview

MCP allows Claude Code to interact with external tools and services through a standardized protocol. MCP servers run as separate processes and expose capabilities (tools, resources, prompts) that Claude can invoke during a session.

This repository uses a **template-based approach** to MCP configuration:

- MCP servers are opt-in (the base template is empty)
- Project-specific templates add relevant servers
- The `setup-project.sh` script merges templates into a final `.mcp.json`

## Available MCP Templates

### base.json

Empty by default. MCP servers are opt-in per project type.

```json
{
  "_source": "base",
  "_version": 1,
  "mcpServers": {}
}
```

### django.json

Adds PostgreSQL MCP server for database introspection and queries.

```json
{
  "_source": "django",
  "_version": 2,
  "mcpServers": {
    "postgres": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-postgres"],
      "env": {
        "POSTGRES_URL": "${DATABASE_URL:-postgresql://localhost:5432/postgres}",
        "POSTGRES_SSL_MODE": "${POSTGRES_SSL_MODE:-disable}"
      }
    }
  }
}
```

**Environment Variables:**

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://localhost:5432/postgres` |
| `POSTGRES_SSL_MODE` | SSL connection mode | `disable` |

**SSL Mode Options:**

- `disable` - No SSL (local development)
- `require` - Require SSL connection
- `verify-ca` - Require SSL and verify server certificate
- `verify-full` - Require SSL and verify server hostname

### react.json

Adds Playwright MCP server for browser automation and testing.

```json
{
  "_source": "react",
  "_version": 1,
  "mcpServers": {
    "playwright": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@playwright/mcp@latest"]
    }
  }
}
```

## Configuration Workflow

### Setting Up MCP for a Project

1. Run `setup-project.sh` with your project templates:

   ```bash
   ~/Development/claude-code-config/scripts/setup-project.sh django
   ```

2. The script generates `.mcp.json` in your project root (not inside `.claude/`)

3. Set required environment variables before starting Claude Code:

   ```bash
   export DATABASE_URL="postgresql://user:pass@localhost:5432/mydb"
   export POSTGRES_SSL_MODE="require"  # for production
   ```

### Preview MCP Configuration

Use `--dry-run` to see what would be generated:

```bash
~/Development/claude-code-config/scripts/setup-project.sh --dry-run django
```

### Check for Configuration Drift

```bash
~/Development/claude-code-config/scripts/setup-project.sh --check django
```

## Environment Variables

MCP templates use shell-style variable expansion with defaults:

```
${VARIABLE:-default_value}
```

Variables are expanded **at Claude Code runtime**, not during template generation. This means:

- You must have the required environment variables set when launching Claude Code
- Use `.envrc` (with direnv) or export variables in your shell profile
- Different environments (dev/staging/prod) can use different values

### Recommended Setup with direnv

Create a `.envrc` in your project root:

```bash
# .envrc
export DATABASE_URL="postgresql://localhost:5432/myproject_dev"
export POSTGRES_SSL_MODE="disable"
```

Then run `direnv allow` to activate.

## Example Usage in Claude Sessions

### PostgreSQL Server

Once configured, you can ask Claude to:

- "Show me the schema for the users table"
- "What indexes exist on the orders table?"
- "Run a query to find all orders from last month"
- "Analyze the foreign key relationships in this database"

### Playwright Server

With Playwright MCP enabled:

- "Take a screenshot of the login page"
- "Click the submit button and wait for the response"
- "Fill in the registration form with test data"
- "Navigate to /dashboard and verify the header text"

## Troubleshooting

### MCP Server Not Starting

1. **Check npx is available:**

   ```bash
   npx --version
   ```

2. **Verify environment variables:**

   ```bash
   echo $DATABASE_URL
   ```

3. **Test the MCP server manually:**

   ```bash
   npx -y @modelcontextprotocol/server-postgres
   ```

### PostgreSQL Connection Errors

1. **Connection refused:**
   - Verify PostgreSQL is running
   - Check the port in `DATABASE_URL`

2. **Authentication failed:**
   - Verify username/password in connection string
   - Check pg_hba.conf allows your connection method

3. **SSL errors:**
   - Set `POSTGRES_SSL_MODE=disable` for local development
   - Set `POSTGRES_SSL_MODE=require` for production

### Playwright Browser Issues

1. **Browser not found:**

   ```bash
   npx playwright install chromium
   ```

2. **Headless mode issues:**
   The Playwright MCP server runs in headless mode by default. Some interactions may behave differently than in a visible browser.

## Creating Custom MCP Templates

To add a new MCP template:

1. Create `mcp-templates/<name>.json`:

   ```json
   {
     "_source": "<name>",
     "_version": 1,
     "mcpServers": {
       "server-name": {
         "type": "stdio",
         "command": "npx",
         "args": ["-y", "@package/mcp-server"]
       }
     }
   }
   ```

2. Update CLAUDE.md to document the new template

3. Test with `--dry-run`:

   ```bash
   ./scripts/setup-project.sh --dry-run <name>
   ```

## Security Considerations

- **Never commit `.mcp.json` with production credentials**
- Use environment variables for all sensitive values
- The `.mcp.json` file should be in `.gitignore`
- SSL should be enabled (`POSTGRES_SSL_MODE=require`) for production databases
- MCP servers run with your user permissions - be cautious with database write access
