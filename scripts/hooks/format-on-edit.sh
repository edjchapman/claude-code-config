#!/usr/bin/env bash
# Auto-format files after Claude edits them (unified Python + JS/TS formatter)
# Used by: PostToolUse hook in settings.json
#
# The harness passes the hook payload as JSON on stdin; the edited file path is
# at .tool_input.file_path. (The older $CLAUDE_FILE_PATH env var is NOT set by
# the harness — relying on it made this hook a silent no-op.) A positional arg
# is still honoured as a fallback for manual runs and tests.
# Only runs if the relevant formatter is available.

set -u

PAYLOAD=$(cat 2> /dev/null || true)

FILE_PATH=""
if [ -n "$PAYLOAD" ] && command -v python3 > /dev/null 2>&1; then
  FILE_PATH=$(printf '%s' "$PAYLOAD" | python3 -c '
import json, sys
try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)
ti = data.get("tool_input") or {}
print(ti.get("file_path") or "")
' 2> /dev/null)
fi
# Fallbacks: legacy env var, then positional arg (manual runs / tests).
FILE_PATH="${FILE_PATH:-${CLAUDE_FILE_PATH:-${1:-}}}"

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
    # Find prettier: check project-local (resolved to git root) first, then global
    GIT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)"
    if [ -n "$GIT_ROOT" ] && [ -f "$GIT_ROOT/node_modules/.bin/prettier" ]; then
      PRETTIER="$GIT_ROOT/node_modules/.bin/prettier"
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
