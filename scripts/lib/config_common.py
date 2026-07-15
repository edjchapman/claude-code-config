"""Shared helpers for the config scripts in scripts/.

Importable because Python puts a script's own directory on sys.path, so the
sibling scripts (merge-settings.py, merge-mcp.py, check-hooks-sync.py) can do:

    from lib.config_common import check_python_version, load_template
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Minimum Python version required by the config scripts
MIN_PYTHON_VERSION = (3, 8)


def check_python_version() -> None:
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


def validate_merged_output(merged: dict) -> None:
    """Validate the merged output is valid JSON and well-formed."""
    try:
        json_str = json.dumps(merged, indent=2)
        json.loads(json_str)
    except (TypeError, ValueError) as e:
        print(f"Error: Generated invalid JSON: {e}", file=sys.stderr)
        sys.exit(1)
