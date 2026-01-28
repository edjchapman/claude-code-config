#!/usr/bin/env python3
"""
Merge multiple Claude settings template files into a single settings.local.json.

Usage: merge-settings.py <templates-dir> <type1> [type2] [type3] ...

Example:
    merge-settings.py ./settings-templates base django react

This will merge base.json, django.json, and react.json into a single output.

Precedence rules:
- deny > allow: If a pattern appears in any deny list, it won't appear in allow
- Later templates override earlier ones for conflicts
"""

import json
import sys
from pathlib import Path

# Minimum Python version required
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

    if "permissions" in template:
        perms = template["permissions"]
        if not isinstance(perms, dict):
            print(f"Error: 'permissions' in '{template_name}' must be an object", file=sys.stderr)
            sys.exit(1)

        for key in ["allow", "deny", "ask"]:
            if key in perms and not isinstance(perms[key], list):
                print(
                    f"Error: 'permissions.{key}' in '{template_name}' must be an array",
                    file=sys.stderr,
                )
                sys.exit(1)


def merge_permissions(templates: list[dict]) -> dict:
    """
    Merge multiple permission templates into one.

    Deny rules take precedence over allow rules.
    """
    # Collect all permissions first
    all_allow: list[str] = []
    all_deny: set[str] = set()
    all_ask: list[str] = []

    seen_allow: set[str] = set()
    seen_ask: set[str] = set()

    # Track highest version across templates
    max_version = 0

    for template in templates:
        # Track version
        version = template.get("_version", 0)
        if version > max_version:
            max_version = version

        perms = template.get("permissions", {})

        # Collect deny rules first (these take absolute precedence)
        for item in perms.get("deny", []):
            all_deny.add(item)

        # Collect allow rules (will filter later)
        for item in perms.get("allow", []):
            if item not in seen_allow:
                seen_allow.add(item)
                all_allow.append(item)

        # Collect ask rules
        for item in perms.get("ask", []):
            if item not in seen_ask:
                seen_ask.add(item)
                all_ask.append(item)

    # Apply precedence: remove any allow rules that match deny patterns
    # For exact matches; pattern matching would require more complex logic
    filtered_allow = [item for item in all_allow if item not in all_deny]

    merged = {
        "_version": max_version,
        "_generated_from": [t.get("_source", "unknown") for t in templates if "_source" in t],
        "permissions": {
            "allow": filtered_allow,
            "deny": sorted(all_deny),
            "ask": all_ask,
        },
    }

    # Clean up empty metadata
    if not merged["_generated_from"]:
        del merged["_generated_from"]

    # Clean up empty permission arrays
    if not merged["permissions"]["ask"]:
        del merged["permissions"]["ask"]

    return merged


def validate_merged_output(merged: dict) -> None:
    """Validate the merged output is valid JSON and well-formed."""
    # Try to serialize and deserialize to ensure valid JSON
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

    # Load and validate all templates
    templates = []
    for name in template_names:
        template = load_template(templates_dir, name)
        validate_template(template, name)
        template["_source"] = name
        templates.append(template)

    # Merge them
    merged = merge_permissions(templates)

    # Validate output
    validate_merged_output(merged)

    # Output as JSON
    print(json.dumps(merged, indent=2))


if __name__ == "__main__":
    main()
