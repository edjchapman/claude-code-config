#!/usr/bin/env bash
# Status line script for Claude Code
# Shows git branch, dirty file count, and open PR status
# Must execute fast (< 1s) — status line refreshes frequently

set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/git-context.sh
. "$SCRIPT_DIR/lib/git-context.sh"

BRANCH=$(git_branch "no-git")
DIRTY=$(git_dirty_count)

# Build status parts
STATUS="$BRANCH"

if [ "$DIRTY" -gt 0 ]; then
  STATUS="$STATUS | ${DIRTY} dirty"
fi

# Open PR status (cached for 60s to stay fast)
CACHE_DIR="${HOME}/.claude/cache"
if command -v md5sum &> /dev/null; then
  CACHE_HASH=$(echo -n "$(pwd)" | md5sum | cut -d' ' -f1)
else
  CACHE_HASH=$(md5 -q -s "$(pwd)" 2> /dev/null || echo "default")
fi
CACHE_FILE="${CACHE_DIR}/pr-status-${CACHE_HASH}"
CACHE_TTL=60
PR_STATUS=""

if [ -f "$CACHE_FILE" ]; then
  CACHE_AGE=$(($(date +%s) - $(stat -f%m "$CACHE_FILE" 2> /dev/null || stat -c%Y "$CACHE_FILE" 2> /dev/null || echo 0)))
  if [ "$CACHE_AGE" -lt "$CACHE_TTL" ]; then
    PR_STATUS=$(cat "$CACHE_FILE")
  fi
fi

if [ -z "$PR_STATUS" ]; then
  if command -v gh &> /dev/null; then
    PR_STATUS=$(gh pr view --json state,number --jq '"PR #\(.number) \(.state)"' 2> /dev/null || echo "no PR")
    mkdir -p "$CACHE_DIR"
    echo "$PR_STATUS" > "$CACHE_FILE" 2> /dev/null
  else
    PR_STATUS="no gh"
  fi
fi

if [ "$PR_STATUS" != "no PR" ] && [ "$PR_STATUS" != "no gh" ]; then
  STATUS="$STATUS | $PR_STATUS"
fi

echo "$STATUS"
