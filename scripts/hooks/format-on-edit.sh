#!/bin/bash
# Auto-format files after Claude edits them (unified Python + JS/TS formatter)
# Used by: PostToolUse hook in settings.json
#
# Expects $CLAUDE_FILE_PATH to be set by the hook system
# Only runs if the relevant formatter is available

FILE_PATH="${CLAUDE_FILE_PATH:-$1}"

# Only run if file exists
[ -f "$FILE_PATH" ] || exit 0

case "$FILE_PATH" in
  *.py)
    # Find ruff: check global first, then project-local venv
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
    $RUFF format --quiet "$FILE_PATH" 2> /dev/null
    $RUFF check --fix --quiet "$FILE_PATH" 2> /dev/null
    ;;
  *.js | *.jsx | *.ts | *.tsx | *.css | *.scss | *.json | *.md)
    # Find prettier: check project-local first, then global
    if [ -f "node_modules/.bin/prettier" ]; then
      PRETTIER="node_modules/.bin/prettier"
    elif command -v prettier &> /dev/null; then
      PRETTIER="prettier"
    else
      exit 0
    fi
    $PRETTIER --write --log-level silent "$FILE_PATH" 2> /dev/null
    ;;
  *)
    exit 0
    ;;
esac

exit 0
