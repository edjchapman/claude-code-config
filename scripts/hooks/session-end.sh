#!/bin/bash
# SessionEnd hook: log session info and clean up
# Used by: SessionEnd hook in settings.json

LOG_DIR="${HOME}/.claude/debug"
LOG_FILE="${LOG_DIR}/session-log.csv"
CACHE_DIR="${HOME}/.claude/cache"

# Ensure log directory exists
mkdir -p "$LOG_DIR" || exit 0

# Create CSV header if file doesn't exist
if [ ! -f "$LOG_FILE" ]; then
  echo "timestamp,working_directory,branch,session_id" > "$LOG_FILE"
fi

# Gather session info
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
WORKING_DIR=$(pwd)
BRANCH=$(git symbolic-ref --short HEAD 2> /dev/null || echo "n/a")
SESSION_ID="${CLAUDE_SESSION_ID:-unknown}"

# Log session
echo "\"${TIMESTAMP}\",\"${WORKING_DIR}\",\"${BRANCH}\",\"${SESSION_ID}\"" >> "$LOG_FILE"

# Clean up cached PR status files older than 1 hour
if [ -d "$CACHE_DIR" ]; then
  find "$CACHE_DIR" -name "pr-status-*" -mmin +60 -delete 2> /dev/null
fi

exit 0
