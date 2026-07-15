#!/usr/bin/env python3
"""
Merge multiple MCP template files into a single .mcp.json.

Usage: merge-mcp.py <templates-dir> <type1> [type2] [type3] ...

Example:
    merge-mcp.py ./mcp-templates base django

This will merge base.json and django.json mcpServers into a single output.

Later templates override earlier ones for server name conflicts.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from lib.config_common import check_python_version, load_template, validate_merged_output


def validate_template(template: dict, template_name: str) -> None:
    """Validate that a template has the expected structure."""
    if not isinstance(template, dict):
        print(f"Error: Template '{template_name}' must be a JSON object", file=sys.stderr)
        sys.exit(1)

    if "mcpServers" in template and not isinstance(template["mcpServers"], dict):
        print(
            f"Error: 'mcpServers' in '{template_name}' must be an object",
            file=sys.stderr,
        )
        sys.exit(1)


def resolve_fragment(templates_dir: Path, server: dict) -> dict:
    """Resolve a {"$fragment": "<name>"} server entry from templates_dir/fragments/.

    Shared server definitions (e.g. the postgres block used by django, fastapi,
    and nextjs) live once under fragments/ instead of being copy-pasted into
    every template. Plain server objects pass through unchanged.
    """
    if set(server.keys()) != {"$fragment"}:
        return server

    fragment_path = templates_dir / "fragments" / f"{server['$fragment']}.json"
    if not fragment_path.exists():
        print(f"Error: Fragment not found: {fragment_path}", file=sys.stderr)
        sys.exit(1)

    try:
        with open(fragment_path) as f:
            return json.loads(f.read())
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {fragment_path}", file=sys.stderr)
        print(f"  Line {e.lineno}, column {e.colno}: {e.msg}", file=sys.stderr)
        sys.exit(1)


def merge_mcp_servers(templates_dir: Path, templates: list) -> dict:
    """Merge multiple MCP templates into one, resolving shared fragments."""
    merged_servers = {}

    for template in templates:
        servers = template.get("mcpServers", {})
        for name, server in servers.items():
            merged_servers[name] = resolve_fragment(templates_dir, server)

    return {"mcpServers": merged_servers}


def main():
    check_python_version()

    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    templates_dir = Path(sys.argv[1])
    template_names = sys.argv[2:]

    if not templates_dir.exists():
        print(f"Error: Templates directory not found: {templates_dir}", file=sys.stderr)
        sys.exit(1)

    if not templates_dir.is_dir():
        print(f"Error: Not a directory: {templates_dir}", file=sys.stderr)
        sys.exit(1)

    templates = []
    for name in template_names:
        template = load_template(templates_dir, name)
        validate_template(template, name)
        templates.append(template)

    merged = merge_mcp_servers(templates_dir, templates)
    validate_merged_output(merged)
    print(json.dumps(merged, indent=2))


if __name__ == "__main__":
    main()
