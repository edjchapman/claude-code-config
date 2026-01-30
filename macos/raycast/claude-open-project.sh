#!/bin/bash

# @raycast.schemaVersion 1
# @raycast.title Open Claude Code
# @raycast.mode silent
# @raycast.packageName Claude Code
# @raycast.icon 🤖
# @raycast.description Open Claude Code in the current Finder directory
# @raycast.argument1 { "type": "text", "placeholder": "Project path (optional)", "optional": true }

PROJECT_DIR="${1:-$(osascript -e 'tell application "Finder" to get POSIX path of (target of front window as text)' 2> /dev/null)}"

if [ -z "$PROJECT_DIR" ]; then
  PROJECT_DIR="$HOME"
fi

open -a Terminal "$PROJECT_DIR"
osascript -e "
  tell application \"Terminal\"
    do script \"cd '$PROJECT_DIR' && claude\" in front window
  end tell
" 2> /dev/null
