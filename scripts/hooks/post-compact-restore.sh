#!/usr/bin/env bash
# Re-inject the pre-compaction state snapshot after context compaction completes.
# Used by: PostCompact hook in settings.json
#
# PostCompact stdout is not shown to the model directly, but a JSON
# hookSpecificOutput.additionalContext payload on stdout IS injected into the
# post-compaction context (verified against the hooks docs, 2026-07-29). We read
# the snapshot that pre-compact-state.sh wrote (keyed by session id) and emit it,
# then remove the one-shot file.

set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/hook-input.sh
. "$SCRIPT_DIR/lib/hook-input.sh"

PAYLOAD=$(cat 2> /dev/null || true)
command -v python3 > /dev/null 2>&1 || exit 0

SESSION_ID=$(hook_field "$PAYLOAD" session_id)
SESSION_ID="${SESSION_ID:-default}"

STATE_FILE="${HOME}/.claude/cache/precompact-${SESSION_ID}.md"
[ -f "$STATE_FILE" ] || exit 0

# Emit the snapshot as additionalContext so the post-compaction turn sees it.
STATE_FILE="$STATE_FILE" python3 <<'PY'
import json, os

path = os.environ["STATE_FILE"]
try:
    with open(path, encoding="utf-8") as fh:
        content = fh.read().strip()
except Exception:
    raise SystemExit(0)

if content:
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PostCompact",
                    "additionalContext": content,
                }
            }
        )
    )
PY

# One-shot: drop the snapshot so it isn't re-injected on a later compaction.
rm -f "$STATE_FILE" 2> /dev/null
exit 0
