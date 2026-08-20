#!/usr/bin/env python3
"""Fail the commit if settings.json grows an unexpected top-level key.

settings.json is symlinked to ~/.claude/settings.json by setup-global.sh,
so anything that writes user-level settings (/model, auto-mode setup,
voice toggles) lands here as a pending diff — in a public repo. Personal,
machine-local, entitlement-gated, or sensitive settings belong in
~/.claude/settings.local.json (higher precedence, untracked); see the
"Settings Files" section of docs/architecture.md.

Adopting a new universal key costs one deliberate line in ALLOWED_KEYS.

Run from anywhere: python3 scripts/check-settings-keys.py
"""

from __future__ import annotations

import json
import sys

from lib.config_common import REPO_ROOT

# Universal, publishable keys settings.json deliberately carries. An
# unlisted key here is far more likely a stray user-level write through
# the symlink than a new shared setting.
ALLOWED_KEYS = {
    "$schema",
    "attribution",
    "fallbackModel",
    "hooks",
    "worktree",
    "statusLine",
    "enabledPlugins",
    "extraKnownMarketplaces",
    "outputStyle",
    "sandbox",
    "tui",
    "autoMemoryEnabled",
    "inputNeededNotifEnabled",
    "agentPushNotifEnabled",
}

SETTINGS = REPO_ROOT / "settings.json"


def main() -> int:
    keys = set(json.loads(SETTINGS.read_text()))
    unknown = sorted(keys - ALLOWED_KEYS)
    for key in unknown:
        print(
            f"FAIL: settings.json: unexpected top-level key `{key}` — personal or"
            " machine-local settings belong in ~/.claude/settings.local.json"
            " (writes here publish through the symlink); to adopt a new universal"
            " key, add it to ALLOWED_KEYS deliberately"
        )
    if unknown:
        return 1

    print(f"settings.json keys OK ({len(keys)} top-level keys, all allowlisted).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
