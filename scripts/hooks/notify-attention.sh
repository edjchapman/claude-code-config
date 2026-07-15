#!/usr/bin/env bash
# Desktop notification when Claude needs your attention
# Used by: Notification hook in settings.json
#
# The Notification event fires when Claude is blocked on you: a permission
# request, or waiting for input while idle. This surfaces it as an OS
# notification so you notice without watching the terminal.
#
# macOS: osascript notification (with sound). Linux: notify-send.
# Fallback everywhere: terminal bell. Always exits 0.

set -u

PAYLOAD=$(cat 2> /dev/null || true)

# Extract the human-readable message from the hook payload; fall back to a
# generic line if the payload is empty or not JSON.
MESSAGE="Claude needs your attention"
if [ -n "$PAYLOAD" ] && command -v python3 > /dev/null 2>&1; then
  EXTRACTED=$(printf '%s' "$PAYLOAD" | python3 -c "
import json, sys
try:
    print(json.loads(sys.stdin.read()).get('message', ''))
except Exception:
    pass
" 2> /dev/null || true)
  [ -n "$EXTRACTED" ] && MESSAGE="$EXTRACTED"
fi

PROJECT=$(basename "$(pwd)")

if command -v osascript > /dev/null 2>&1; then
  # macOS - osascript strings are quote-sensitive; strip double quotes
  SAFE_MESSAGE=$(printf '%s' "$MESSAGE" | tr -d '"' | head -c 200)
  osascript -e "display notification \"$SAFE_MESSAGE\" with title \"Claude Code\" subtitle \"$PROJECT\" sound name \"Glass\"" > /dev/null 2>&1 || printf '\a'
elif command -v notify-send > /dev/null 2>&1; then
  # Linux desktop
  notify-send "Claude Code — $PROJECT" "$MESSAGE" > /dev/null 2>&1 || printf '\a'
else
  # No notification daemon: terminal bell
  printf '\a'
fi

exit 0
