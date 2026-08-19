"""Shared helpers for the config scripts in scripts/.

Importable because Python puts a script's own directory on sys.path, so the
sibling scripts (merge-settings.py, merge-mcp.py, generate.py) can do:

    from lib.config_common import check_python_version, load_template
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

# Minimum Python version required by the config scripts
MIN_PYTHON_VERSION = (3, 8)


class GenerationError(Exception):
    """A generator target's sources are missing or malformed (see generate.py)."""


def load_json(path: Path) -> dict:
    """Load a JSON source for a generator target; raises GenerationError."""
    if not path.is_file():
        raise GenerationError(f"source not found: {path}")
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise GenerationError(f"invalid JSON in {path}: {exc}") from exc


def parse_frontmatter(path: Path) -> dict:
    """Parse simple YAML frontmatter into {key: str | list[str]}.

    Handles the styles used in this repo without a PyYAML dependency: plain
    single-line scalars, block scalars (`>-`, `>`, `|`, `|-`) whose value is
    the following indented lines joined with spaces, and simple string lists
    (`- item` lines under a bare key). Derived from the description parser
    that previously lived in check-context-budget.py, which now consumes this.
    """
    lines = path.read_text().splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    try:
        end = next(i for i, line in enumerate(lines[1:], start=1) if line.strip() == "---")
    except StopIteration:
        return {}
    block = lines[1:end]
    result: dict = {}
    i = 0
    while i < len(block):
        match = re.match(r"^([A-Za-z][A-Za-z0-9_-]*):(.*)$", block[i])
        if not match:
            i += 1
            continue
        key, value = match.group(1), match.group(2).strip()
        if value in {">", ">-", "|", "|-"}:
            collected = []
            i += 1
            while i < len(block) and (block[i].startswith((" ", "\t")) or block[i].strip() == ""):
                collected.append(block[i].strip())
                i += 1
            result[key] = " ".join(collected).strip()
            continue
        if value == "":
            items = []
            j = i + 1
            while j < len(block) and block[j].lstrip().startswith("- "):
                items.append(_unquote(block[j].lstrip()[2:].strip()))
                j += 1
            if items:
                result[key] = items
                i = j
                continue
        result[key] = _unquote(value)
        i += 1
    return result


def _unquote(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


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
