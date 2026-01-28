#!/bin/bash
# Auto-format JS/TS/CSS/JSON files after Claude edits them
# Used by: PostToolUse hook in settings.json
#
# Expects $CLAUDE_FILE_PATH to be set by the hook system
# Only runs if prettier is available in the project

FILE_PATH="${CLAUDE_FILE_PATH:-$1}"

# Only process supported file types
case "$FILE_PATH" in
  *.js | *.jsx | *.ts | *.tsx | *.css | *.scss | *.json | *.md) ;;
  *) exit 0 ;;
esac

# Only run if file exists
[ -f "$FILE_PATH" ] || exit 0

# Check for local prettier (prefer project-local)
if [ -f "node_modules/.bin/prettier" ]; then
  PRETTIER="node_modules/.bin/prettier"
elif command -v prettier &> /dev/null; then
  PRETTIER="prettier"
else
  exit 0
fi

# Format the file
$PRETTIER --write --log-level silent "$FILE_PATH" 2> /dev/null

exit 0
