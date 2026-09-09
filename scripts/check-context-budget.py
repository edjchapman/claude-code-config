#!/usr/bin/env python3
"""Fail CI if the always-loaded context surface exceeds its byte budget.

Every session pays a fixed token cost for: the global memory file
(home/CLAUDE.md), the frontmatter `description:` of every skill and
agent (bodies load on demand and are deliberately not counted), and the
model-invocable descriptions of every **third-party primitive** a pinned
plugin ships (read from the lockfile, since the plugin cache is a local
artifact absent in CI). A skill costs the same whether this repo authored
it or merely enabled it, so both are counted. This check keeps that
surface from growing silently — see the "What earns always-loaded
context" ladder in docs/extending.md.

Per-item descriptions over WARN_ITEM_BYTES get a warning (exit 0),
unless ACCEPTED_OVERSIZE_ITEMS records a reviewed size for that item;
a total over TOTAL_BUDGET_BYTES fails the check (exit 1).

Run from anywhere: python3 scripts/check-context-budget.py
"""

from __future__ import annotations

import sys
from pathlib import Path

from lib import vendored_plugins
from lib.config_common import REPO_ROOT, parse_frontmatter, tracked_files

# Raised from 10_240 in #152: moving the vendored plugin to a tag (ADR-0003,
# revised) made two more of its skills model-invocable on a surface already at
# the line. Raised by half a KiB rather than a round KiB so the next addition
# still has to argue; the lockfile's always_loaded_bytes and this script's
# printed Total carry the actual figures.
TOTAL_BUDGET_BYTES = 10_752
WARN_ITEM_BYTES = 350

# Third-party descriptions this repo has reviewed and accepted above the
# per-item guideline, keyed by their budget label with the accepted size in
# bytes. An entry silences the warning at exactly that size and no larger, so
# an upstream bump that grows the description warns again and forces a fresh
# decision. A third-party primitive cannot be trimmed, and it cannot be demoted
# either: `skillOverrides` is inert for plugin-sourced skills (verified against
# Claude Code 2.1.266 for #159 — the resolver returns `on` for any skill with
# source "plugin" before it reads the setting, and /skills shows the entry
# locked). The only remaining lever is dropping the pin, so an accepted size
# is the honest record of "we keep it, at this cost".
ACCEPTED_OVERSIZE_ITEMS: dict[str, int] = {
    # Kept for its Spec axis (review against the originating issue), which the
    # bundled /code-review lacks and /implement depends on. #159.
    "mattpocock-skills:code-review (description)": 420,
}

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

    for path in tracked_files(":(glob)skills/*/SKILL.md") + tracked_files(":(glob)agents/*.md"):
        rel = str(path.relative_to(REPO_ROOT))
        desc = frontmatter_description(path)
        if not desc:
            print(f"WARNING: {rel} has no parseable description: frontmatter")
            continue
        items.append((f"{rel} (description)", len(desc.encode())))

    items.extend(vendored_plugins.always_loaded_items(REPO_ROOT))

    memory_name = str(GLOBAL_MEMORY.relative_to(REPO_ROOT))
    total = sum(size for _, size in items)
    width = max(len(name) for name, _ in items)

    def over_threshold(name: str, size: int) -> bool:
        if name == memory_name:
            return False
        return size > ACCEPTED_OVERSIZE_ITEMS.get(name, WARN_ITEM_BYTES)

    print("Always-loaded context surface:")
    for name, size in sorted(items, key=lambda item: -item[1]):
        if over_threshold(name, size):
            marker = "  <-- over per-item warn threshold"
        elif name in ACCEPTED_OVERSIZE_ITEMS:
            marker = "  (accepted oversize, #159)"
        else:
            marker = ""
        print(f"  {name:<{width}}  {size:>6} B{marker}")
    print(f"\nTotal: {total} B (budget {TOTAL_BUDGET_BYTES} B, per-item warn {WARN_ITEM_BYTES} B)")

    # A third-party primitive cannot be trimmed — this repo does not own its
    # frontmatter — so it gets the advice that actually applies to it.
    vendored = {name for name, _ in vendored_plugins.always_loaded_items(REPO_ROOT)}
    for name, size in items:
        if not over_threshold(name, size):
            continue
        if name in ACCEPTED_OVERSIZE_ITEMS:
            remedy = (
                f"it grew past its accepted {ACCEPTED_OVERSIZE_ITEMS[name]} B — "
                "re-review it (update ACCEPTED_OVERSIZE_ITEMS) or drop the pin"
            )
        elif name in vendored:
            remedy = (
                "drop the pin or accept it in ACCEPTED_OVERSIZE_ITEMS "
                "(skillOverrides is inert for plugin skills)"
            )
        else:
            remedy = "trim it or justify the cost"
        print(f"WARNING: {name} exceeds {WARN_ITEM_BYTES} B — {remedy}")

    if total > TOTAL_BUDGET_BYTES:
        print(f"FAIL: always-loaded surface {total} B exceeds the {TOTAL_BUDGET_BYTES} B budget.")
        print("Trim descriptions, demote content down the ladder (docs/extending.md),")
        print("or raise the budget here with a justification in the same commit.")
        return 1

    print("Context budget OK.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
