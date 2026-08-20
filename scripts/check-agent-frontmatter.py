#!/usr/bin/env python3
"""Fail CI if an agent definition's frontmatter breaks its contract.

The frontmatter is the interface every consumer of agents/*.md relies on:
the Claude Code runtime routes on it, readme_catalogs.py renders it, and
check-context-budget.py budgets it. Its invariants were previously enforced
only by convention, so a typo'd key (`permisionMode:`) or a frontmatter
`name:` drifting from the filename would ship silently — the runtime
ignores unknown keys, and check-duplicates.sh compares filenames only.

Checks per agent file:
  - frontmatter exists, with non-empty `name:` and `description:`
  - `name:` equals the filename stem (one source of truth for identity)
  - every key is in ALLOWED_KEYS (catches misspelled runtime keys)

Run from anywhere: python3 scripts/check-agent-frontmatter.py
"""

from __future__ import annotations

import sys
from pathlib import Path

from lib.config_common import REPO_ROOT, parse_frontmatter, tracked_files

# Runtime keys this repo's agents actually use. Grow this deliberately when
# adopting a new Claude Code frontmatter key — an unknown key here is far
# more likely a typo than a new feature.
ALLOWED_KEYS = {"name", "description", "model", "color", "memory", "permissionMode", "tools"}
REQUIRED_KEYS = {"name", "description"}


def check_agent(path: Path) -> list[str]:
    """All contract violations in one agent file, as printable messages."""
    rel = str(path.relative_to(REPO_ROOT))
    frontmatter = parse_frontmatter(path)
    if not frontmatter:
        return [f"{rel}: no parseable frontmatter block"]

    errors = []
    for key in sorted(REQUIRED_KEYS - frontmatter.keys()):
        errors.append(f"{rel}: missing required key `{key}:`")
    for key in sorted(k for k in REQUIRED_KEYS & frontmatter.keys() if not frontmatter[k]):
        errors.append(f"{rel}: required key `{key}:` is empty")
    for key in sorted(frontmatter.keys() - ALLOWED_KEYS):
        errors.append(f"{rel}: unknown key `{key}:` — typo, or add it to ALLOWED_KEYS")

    name = frontmatter.get("name", "")
    if name and name != path.stem:
        errors.append(f"{rel}: `name: {name}` does not match filename stem `{path.stem}`")
    return errors


def main() -> int:
    files = tracked_files("agents/*.md")
    if not files:
        print("FAIL: no tracked agent files found under agents/")
        return 1

    errors = [error for path in files for error in check_agent(path)]
    for error in errors:
        print(f"FAIL: {error}")
    if errors:
        return 1

    print(f"Agent frontmatter OK ({len(files)} files checked).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
