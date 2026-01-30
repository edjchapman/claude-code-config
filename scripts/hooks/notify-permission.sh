#!/bin/bash
# Send macOS notification when Claude needs permission
# Used by: Notification (permission_prompt) hook in settings.json
#
# Parses stdin JSON for tool details when available.
# Only works on macOS. Silently exits on other platforms.

# Only run on macOS
if [ "$(uname)" != "Darwin" ]; then
  exit 0
fi

# Try to parse tool details from stdin JSON
TITLE="Claude Code"
MESSAGE="Claude Code needs your permission to continue"

if [ -t 0 ]; then
  # No stdin, use default message
  :
else
  INPUT=$(cat 2> /dev/null || true)
  if [ -n "$INPUT" ]; then
    # Try to extract tool name from JSON
    TOOL_NAME=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_name', d.get('tool', '')))" 2> /dev/null || true)
    if [ -n "$TOOL_NAME" ]; then
      MESSAGE="Permission needed for: $TOOL_NAME"
    fi
  fi
fi

# Use terminal-notifier if available (supports action buttons), fall back to osascript
if command -v terminal-notifier &> /dev/null; then
  terminal-notifier \
    -title "$TITLE" \
    -message "$MESSAGE" \
    -sound Ping \
    -group "claude-code-permission" \
    -activate com.apple.Terminal \
    2> /dev/null
else
  SAFE_MESSAGE="${MESSAGE//\"/\\\"}"
  SAFE_TITLE="${TITLE//\"/\\\"}"
  osascript -e "display notification \"$SAFE_MESSAGE\" with title \"$SAFE_TITLE\" sound name \"Ping\"" 2> /dev/null
fi

exit 0
