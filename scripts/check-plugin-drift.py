#!/usr/bin/env python3
"""Fail when the local marketplace clone has moved off the commit the lockfile records.

The vendored plugin is pinned to a tag, because Claude Code cannot clone a
commit SHA, and a tag can be re-cut. The lockfile therefore records the
commit the tag resolved to when the lockfile diff was reviewed. If the
clone on this machine is no longer at that commit, what loads into a
session is not what was reviewed, while settings.json and the lockfile
still agree and `generate.py --check` still passes.

Local-only by nature: the clone is a machine artifact under
~/.claude/plugins. Where there is none (CI, a machine without the plugin)
the check says it skipped and exits 0.

Run from anywhere: python3 scripts/check-plugin-drift.py
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from lib.config_common import REPO_ROOT
from lib.vendored_plugins import LOCKFILE, MARKETPLACE_CLONES, clone_commit, load_lock


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=REPO_ROOT, help="repo root override")
    parser.add_argument(
        "--marketplaces",
        type=Path,
        default=MARKETPLACE_CLONES,
        help="marketplace clones directory override (tests)",
    )
    args = parser.parse_args()

    lock = load_lock(args.root)
    if lock is None:
        print(f"SKIPPED: no {LOCKFILE}, so this repo pins no plugin.")
        return 0

    clone = args.marketplaces / lock["marketplace"]
    head = clone_commit(clone)
    if head is None:
        print(
            f"SKIPPED: no marketplace clone at {clone} — clone drift not checked "
            "(expected in CI and on a machine without the plugin)."
        )
        return 0

    locked = lock.get("commit")
    if head == locked:
        print(f"Marketplace clone OK ({lock['marketplace']} at {lock['ref']}, {head[:12]}).")
        return 0

    print(f"FAIL: marketplace clone drift for {lock['marketplace']} (pinned at {lock['ref']}).")
    print(f"  {LOCKFILE} records  {locked}")
    print(f"  {clone} is at  {head}")
    print("What loads into a session is not what the lockfile diff reviewed.")
    print("If you moved the pin, finish the bump: regenerate the lockfile and read the diff")
    print('(docs/extending.md, "Bumping a vendored plugin"). If you did not, upstream may')
    print(f"have re-cut {lock['ref']} — review what changed before regenerating.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
