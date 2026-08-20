#!/usr/bin/env bash
# Warn when ~/.claude/settings.json has drifted from the repo's settings.json
#
# Why: settings.json is mirrored — not symlinked — into ~/.claude/settings.json
# (ADR-0002), so a repo edit stays inert until a sync runs, and a runtime write
# can flip a managed key. This check surfaces pending drift at session
# start. Warn-only by design: it never applies changes itself, because silent
# mutation of the user's settings was deliberately rejected.

set -u

# Symlink-mode installs only: plugin-mode users don't consume settings.json.
[ -L ~/.claude/agents ] || exit 0

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

[ -f "$REPO_ROOT/scripts/sync-global-settings.py" ] || exit 0
command -v python3 >/dev/null 2>&1 || exit 0

python3 "$REPO_ROOT/scripts/sync-global-settings.py" --check 2>/dev/null || true
