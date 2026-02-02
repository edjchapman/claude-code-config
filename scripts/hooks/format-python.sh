#!/bin/bash
# Auto-format Python files after Claude edits them
# Used by: PostToolUse hook in settings.json
#
# Expects $CLAUDE_FILE_PATH to be set by the hook system
# Only runs if ruff is available

FILE_PATH="${CLAUDE_FILE_PATH:-$1}"

# Only process .py files
case "$FILE_PATH" in
  *.py) ;;
  *) exit 0 ;;
esac

# Only run if file exists
[ -f "$FILE_PATH" ] || exit 0

# Only run if ruff is available (check global first, then project-local venv)
if command -v ruff &> /dev/null; then
  RUFF="ruff"
else
  GIT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)"
  if [ -n "$GIT_ROOT" ] && [ -f "$GIT_ROOT/.venv/bin/ruff" ]; then
    RUFF="$GIT_ROOT/.venv/bin/ruff"
  else
    exit 0
  fi
fi

# Format the file
$RUFF format --quiet "$FILE_PATH" 2> /dev/null

# Fix auto-fixable lint issues
$RUFF check --fix --quiet "$FILE_PATH" 2> /dev/null

exit 0
