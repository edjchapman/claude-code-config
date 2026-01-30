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

MIN_PYTHON_VERSION = (3, 8)


def check_python_version():
    """Ensure we're running on a supported Python version."""
    if sys.version_info < MIN_PYTHON_VERSION:
        print(
            f"Error: Python {MIN_PYTHON_VERSION[0]}.{MIN_PYTHON_VERSION[1]}+ required, "
            f"but running {sys.version_info.major}.{sys.version_info.minor}",
            file=sys.stderr,
        )
        sys.exit(1)


def load_template(templates_dir: Path, template_name: str) -> dict:
    """Load a template file and return its contents."""
    template_path = templates_dir / f"{template_name}.json"
    if not template_path.exists():
        print(f"Error: Template not found: {template_path}", file=sys.stderr)
        print(f"Hint: Run 'ls {templates_dir}' to see available templates", file=sys.stderr)
        sys.exit(1)

    try:
        with open(template_path) as f:
            content = f.read()
            if not content.strip():
                print(f"Error: Template file is empty: {template_path}", file=sys.stderr)
                sys.exit(1)
            return json.loads(content)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {template_path}", file=sys.stderr)
        print(f"  Line {e.lineno}, column {e.colno}: {e.msg}", file=sys.stderr)
        sys.exit(1)
    except PermissionError:
        print(f"Error: Permission denied reading {template_path}", file=sys.stderr)
        sys.exit(1)


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


def merge_mcp_servers(templates: list) -> dict:
    """Merge multiple MCP templates into one."""
    merged_servers = {}

    for template in templates:
        servers = template.get("mcpServers", {})
        merged_servers.update(servers)

    return {"mcpServers": merged_servers}


def validate_merged_output(merged: dict) -> None:
    """Validate the merged output is valid JSON and well-formed."""
    try:
        json_str = json.dumps(merged, indent=2)
        json.loads(json_str)
    except (TypeError, ValueError) as e:
        print(f"Error: Generated invalid JSON: {e}", file=sys.stderr)
        sys.exit(1)


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

    merged = merge_mcp_servers(templates)
    validate_merged_output(merged)
    print(json.dumps(merged, indent=2))


if __name__ == "__main__":
    main()
