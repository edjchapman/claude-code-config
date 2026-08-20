#!/usr/bin/env python3
"""Fail the commit if settings.json grows an unexpected top-level key.

settings.json is mirrored into ~/.claude/settings.json by
scripts/sync-global-settings.py (ADR-0002), so every key committed here
propagates to every consumer's user scope on their next sync. Personal,
machine-local, entitlement-gated, or sensitive settings (model pins,
permissions, ...) belong directly in ~/.claude/settings.json as unmanaged
keys — the sync preserves those; see the "Settings Files" section of
docs/architecture.md.

Adopting a new universal key costs one deliberate line in ALLOWED_KEYS
(scripts/lib/settings_keys.py).

Run from anywhere: python3 scripts/check-settings-keys.py
"""

from __future__ import annotations

import json
import sys

from lib.config_common import REPO_ROOT
from lib.settings_keys import ALLOWED_KEYS

SETTINGS = REPO_ROOT / "settings.json"


def main() -> int:
    keys = set(json.loads(SETTINGS.read_text()))
    unknown = sorted(keys - ALLOWED_KEYS)
    for key in unknown:
        print(
            f"FAIL: settings.json: unexpected top-level key `{key}` — personal or"
            " machine-local settings belong in ~/.claude/settings.json as"
            " unmanaged keys (the sync mirror preserves them; ADR-0002); to adopt"
            " a new universal key, add it to ALLOWED_KEYS in"
            " scripts/lib/settings_keys.py deliberately"
        )
    if unknown:
        return 1

    print(f"settings.json keys OK ({len(keys)} top-level keys, all allowlisted).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
