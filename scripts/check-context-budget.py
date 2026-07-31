#!/usr/bin/env python3
"""Fail CI if the always-loaded context surface exceeds its byte budget.

Every session pays a fixed token cost for: the global memory file
(home/CLAUDE.md) and the frontmatter `description:` of every skill and
agent (bodies load on demand and are deliberately not counted). This
check keeps that surface from growing silently — see the "What earns
always-loaded context" ladder in docs/extending.md.

Per-item descriptions over WARN_ITEM_BYTES get a warning (exit 0);
a total over TOTAL_BUDGET_BYTES fails the check (exit 1).

Files are enumerated via `git ls-files` (matching check-docs-drift.sh)
so untracked local-only extras never trip CI.

Run from anywhere: python3 scripts/check-context-budget.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

TOTAL_BUDGET_BYTES = 10_240
WARN_ITEM_BYTES = 350

REPO_ROOT = Path(__file__).resolve().parent.parent
GLOBAL_MEMORY = REPO_ROOT / "home" / "CLAUDE.md"


def tracked_files(pattern: str) -> list[Path]:
    out = subprocess.run(
        ["git", "ls-files", pattern],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    paths = [REPO_ROOT / line for line in out.splitlines() if line]
    # ls-files reads the index; a file deleted in the worktree but not yet
    # committed would otherwise crash the read below.
    return [p for p in paths if p.is_file()]


def frontmatter_description(path: Path) -> str:
    """Extract the `description:` value from YAML frontmatter.

    Handles the two styles used in this repo: a plain single-line scalar,
    and block scalars (`>-`, `>`, `|`, `|-`) whose value is the following
    indented lines. Avoids a PyYAML dependency so CI needs no installs.
    """
    lines = path.read_text().splitlines()
    if not lines or lines[0].strip() != "---":
        return ""
    try:
        end = next(i for i, line in enumerate(lines[1:], start=1) if line.strip() == "---")
    except StopIteration:
        return ""
    block = lines[1:end]
    for i, line in enumerate(block):
        if not line.startswith("description:"):
            continue
        value = line.split(":", 1)[1].strip()
        if value not in {">", ">-", "|", "|-"}:
            return value
        collected = []
        for cont in block[i + 1 :]:
            if cont.startswith((" ", "\t")):
                collected.append(cont.strip())
            elif cont.strip() == "":
                collected.append("")
            else:
                break
        return " ".join(collected).strip()
    return ""


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
