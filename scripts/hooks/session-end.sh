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

# --- Daily log: append git session summary ---
# Only runs if inside a git repo with recent commits
if git rev-parse --is-inside-work-tree > /dev/null 2>&1; then
  GIT_USER=$(git config user.name 2> /dev/null)
  if [ -n "$GIT_USER" ]; then
    # macOS date uses -v, GNU date uses -d
    if date -v-2H +%s > /dev/null 2>&1; then
      SINCE=$(date -v-2H +"%Y-%m-%dT%H:%M:%S")
    else
      SINCE=$(date -d '2 hours ago' +"%Y-%m-%dT%H:%M:%S")
    fi

    COMMITS=$(git log --since="$SINCE" --author="$GIT_USER" --oneline 2> /dev/null)
    if [ -n "$COMMITS" ]; then
      STANDUPS_DIR="./standups"
      TODAY=$(date +"%Y-%m-%d")
      DAILY_LOG="${STANDUPS_DIR}/${TODAY}-log.md"
      SESSION_TIME=$(date +"%H:%M")

      mkdir -p "$STANDUPS_DIR"

      # Create log file with header if it doesn't exist
      if [ ! -f "$DAILY_LOG" ]; then
        HEADER_DATE=$(date +"%d %b %Y")
        printf "# Daily Log - %s\n" "$HEADER_DATE" > "$DAILY_LOG"
      fi

      # Ensure Session Summaries section exists
      if ! grep -q "^## Session Summaries" "$DAILY_LOG" 2> /dev/null; then
        printf "\n## Session Summaries\n" >> "$DAILY_LOG"
      fi

      # Append session block
      {
        printf "\n### Session @ %s (branch: %s)\n" "$SESSION_TIME" "$BRANCH"
        echo "$COMMITS" | while IFS= read -r line; do
          printf -- "- %s\n" "$line"
        done
      } >> "$DAILY_LOG"
    fi
  fi
fi

# Clean up cached PR status files older than 1 hour
if [ -d "$CACHE_DIR" ]; then
  find "$CACHE_DIR" -name "pr-status-*" -mmin +60 -delete 2> /dev/null
fi

exit 0
