#!/usr/bin/env python3
"""
Verify that the hook configuration stays in sync across both consumption modes.

The repo is consumable two ways (see CLAUDE.md "Hooks"):
  - settings.json  -> read by the symlink-global install path (its "hooks" key)
  - hooks/hooks.json -> read by the plugin install path (its "hooks" key)

These two hook blocks MUST be identical. This script fails (exit 1) if they drift,
naming exactly which events differ so the fix is obvious. It is wired into CI
(.github/workflows/validate-config.yml) alongside check-duplicates.sh.

Usage: check-hooks-sync.py [settings.json] [hooks/hooks.json]

With no arguments it resolves both files relative to the repo root (the parent of
this script's directory), so it works from any working directory and in CI.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from lib.config_common import check_python_version

# Repo root = parent of the scripts/ directory this file lives in.
REPO_ROOT = Path(__file__).resolve().parent.parent


def load_hooks(path: Path) -> dict:
    """Load a JSON file and return its top-level 'hooks' object."""
    if not path.exists():
        print(f"Error: File not found: {path}", file=sys.stderr)
        sys.exit(1)

    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {path}", file=sys.stderr)
        print(f"  Line {e.lineno}, column {e.colno}: {e.msg}", file=sys.stderr)
        sys.exit(1)

    if "hooks" not in data:
        print(f"Error: No 'hooks' key in {path}", file=sys.stderr)
        sys.exit(1)

    return data["hooks"]


def report_drift(settings_hooks: dict, plugin_hooks: dict) -> None:
    """Print a human-readable breakdown of how the two hook blocks differ."""
    settings_events = set(settings_hooks)
    plugin_events = set(plugin_hooks)

    only_settings = settings_events - plugin_events
    only_plugin = plugin_events - settings_events
    if only_settings:
        print(f"  Only in settings.json:   {sorted(only_settings)}", file=sys.stderr)
    if only_plugin:
        print(f"  Only in hooks/hooks.json: {sorted(only_plugin)}", file=sys.stderr)

    for event in sorted(settings_events & plugin_events):
        if settings_hooks[event] != plugin_hooks[event]:
            print(f"  Event '{event}' differs:", file=sys.stderr)
            print(f"    settings.json:   {json.dumps(settings_hooks[event])}", file=sys.stderr)
            print(f"    hooks/hooks.json: {json.dumps(plugin_hooks[event])}", file=sys.stderr)


def main() -> None:
    check_python_version()

    settings_path = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO_ROOT / "settings.json"
    plugin_path = Path(sys.argv[2]) if len(sys.argv) > 2 else REPO_ROOT / "hooks" / "hooks.json"

    settings_hooks = load_hooks(settings_path)
    plugin_hooks = load_hooks(plugin_path)

    if settings_hooks == plugin_hooks:
        print("✓ Hook config is in sync (settings.json <-> hooks/hooks.json)")
        return

    print(
        "✗ Hook config DRIFT: settings.json 'hooks' != hooks/hooks.json 'hooks'.",
        file=sys.stderr,
    )
    print("  Keep both files identical (see CLAUDE.md 'Hooks').", file=sys.stderr)
    report_drift(settings_hooks, plugin_hooks)
    sys.exit(1)


if __name__ == "__main__":
    main()
