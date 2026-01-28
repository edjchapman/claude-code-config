#!/bin/bash
# Send macOS notification when Claude needs permission
# Used by: Notification (permission_prompt) hook in settings.json
#
# Only works on macOS. Silently exits on other platforms.

# Only run on macOS
if [ "$(uname)" != "Darwin" ]; then
  exit 0
fi

osascript -e 'display notification "Claude Code needs your permission to continue" with title "Claude Code" sound name "Ping"' 2> /dev/null

exit 0
