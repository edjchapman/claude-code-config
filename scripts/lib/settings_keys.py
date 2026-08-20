"""The managed top-level key sets for the repo's settings.json (ADR-0002).

Two consumers derive from these sets — one source of truth for what the
repo manages:

- ``check-settings-keys.py`` fails a commit when settings.json grows a key
  not in ALLOWED_KEYS (almost always a stray user-scope write).
- ``sync-global-settings.py`` mirrors exactly these keys into
  ``~/.claude/settings.json`` and treats every other key there as personal
  (never touched by a sync).
"""

from __future__ import annotations

# Universal, publishable keys settings.json deliberately carries. An
# unlisted key is far more likely a stray user-scope write than a new
# shared setting; adopting one costs a deliberate line here.
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

# Tombstones: keys the repo once managed and has since retired. A sync
# deletes these from ~/.claude/settings.json once, so a dropped key does
# not linger on consumer machines. Move a key here when removing it from
# both settings.json and ALLOWED_KEYS.
#
# Never list a personal key here (model, permissions, ...): the sync would
# delete the user's own setting on every run.
RETIRED_KEYS: set[str] = set()
