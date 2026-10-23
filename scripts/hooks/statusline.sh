#!/usr/bin/env bash
# Status line script for Claude Code
# Line 1: git branch, dirty file count, open PR; line 2: model, context use, effort
# Why: everything but the dirty count arrives in the stdin JSON payload, so the
# script makes no network calls and keeps no cache — it stays well under the 300ms
# debounce that Claude Code refreshes on.

set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/git-context.sh
. "$SCRIPT_DIR/lib/git-context.sh"

PAYLOAD=$(cat 2> /dev/null || true)

# One python3 pass over the payload; absent fields come back empty. The unit
# separator (not tab) keeps empty fields from collapsing in read.
IFS=$'\x1f' read -r DIR PR_NUM PR_STATE MODEL CTX EFFORT < <(
  printf '%s' "$PAYLOAD" | python3 -c '
import json, sys
try:
    d = json.load(sys.stdin)
except Exception:
    d = {}
def get(path):
    cur = d
    for part in path.split("."):
        cur = cur.get(part) if isinstance(cur, dict) else None
    return "" if cur is None else str(cur)
ctx = get("context_window.used_percentage")
if ctx:
    ctx = str(round(float(ctx)))
print("\x1f".join([get("workspace.current_dir"), get("pr.number"), get("pr.review_state"),
                 get("model.display_name"), ctx, get("effort.level")]))
' 2> /dev/null || echo
)

if [ -n "$DIR" ]; then
  cd "$DIR" 2> /dev/null || true
fi

LINE1=$(git_branch "no-git")
DIRTY=$(git_dirty_count)
[ "$DIRTY" -gt 0 ] && LINE1="$LINE1 | ${DIRTY} dirty"
[ -n "$PR_NUM" ] && LINE1="$LINE1 | PR #${PR_NUM}${PR_STATE:+ $PR_STATE}"
echo "$LINE1"

LINE2="$MODEL"
if [ -n "$CTX" ]; then
  if [ "$CTX" -ge 80 ]; then
    COLOR='\033[31m'
  elif [ "$CTX" -ge 50 ]; then
    COLOR='\033[33m'
  else
    COLOR='\033[32m'
  fi
  LINE2="${LINE2:+$LINE2 · }$(printf "${COLOR}%s%% ctx\033[0m" "$CTX")"
fi
[ -n "$EFFORT" ] && LINE2="${LINE2:+$LINE2 · }$EFFORT effort"
[ -n "$LINE2" ] && echo "$LINE2"

exit 0
