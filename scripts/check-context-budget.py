#!/usr/bin/env python3
"""Fail CI if the always-loaded context surface exceeds its byte budget.

Every session pays a fixed token cost for: the global memory file
(home/CLAUDE.md) and the frontmatter `description:` of every skill and
agent (bodies load on demand and are deliberately not counted). This
check keeps that surface from growing silently — see the "What earns
always-loaded context" ladder in docs/extending.md.

Per-item descriptions over WARN_ITEM_BYTES get a warning (exit 0);
a total over TOTAL_BUDGET_BYTES fails the check (exit 1).

Run from anywhere: python3 scripts/check-context-budget.py
"""

from __future__ import annotations

import sys
from pathlib import Path

from lib.config_common import REPO_ROOT, parse_frontmatter, tracked_files

TOTAL_BUDGET_BYTES = 10_240
WARN_ITEM_BYTES = 350

GLOBAL_MEMORY = REPO_ROOT / "home" / "CLAUDE.md"


def frontmatter_description(path: Path) -> str:
    """Extract the `description:` value from YAML frontmatter.

    The parser lives in lib/config_common.py (shared with generate.py's
    catalog targets). Avoids a PyYAML dependency so CI needs no installs.
    """
    value = parse_frontmatter(path).get("description", "")
    return value if isinstance(value, str) else ""


def main() -> int:
    items: list[tuple[str, int]] = []

    items.append((str(GLOBAL_MEMORY.relative_to(REPO_ROOT)), len(GLOBAL_MEMORY.read_bytes())))

    for path in tracked_files("skills/*/SKILL.md") + tracked_files("agents/*.md"):
        rel = str(path.relative_to(REPO_ROOT))
        desc = frontmatter_description(path)
        if not desc:
            print(f"WARNING: {rel} has no parseable description: frontmatter")
            continue
        items.append((f"{rel} (description)", len(desc.encode())))

    memory_name = str(GLOBAL_MEMORY.relative_to(REPO_ROOT))
    total = sum(size for _, size in items)
    width = max(len(name) for name, _ in items)

    print("Always-loaded context surface:")
    for name, size in sorted(items, key=lambda item: -item[1]):
        flagged = size > WARN_ITEM_BYTES and name != memory_name
        marker = "  <-- over per-item warn threshold" if flagged else ""
        print(f"  {name:<{width}}  {size:>6} B{marker}")
    print(f"\nTotal: {total} B (budget {TOTAL_BUDGET_BYTES} B, per-item warn {WARN_ITEM_BYTES} B)")

    over = [name for name, size in items if size > WARN_ITEM_BYTES and name != memory_name]
    for name in over:
        print(f"WARNING: {name} exceeds {WARN_ITEM_BYTES} B — trim it or justify the cost")

    if total > TOTAL_BUDGET_BYTES:
        print(f"FAIL: always-loaded surface {total} B exceeds the {TOTAL_BUDGET_BYTES} B budget.")
        print("Trim descriptions, demote content down the ladder (docs/extending.md),")
        print("or raise the budget here with a justification in the same commit.")
        return 1

    print("Context budget OK.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
