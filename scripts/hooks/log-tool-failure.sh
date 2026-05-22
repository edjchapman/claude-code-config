#!/bin/bash
# Append failed tool calls to a JSONL log for later pattern analysis
# Used by: PostToolUseFailure hook in settings.json
#
# Cheap, no LLM. Helps spot which tools fail most so you can pre-allow them
# or fix the underlying issue.

set -u

LOG_DIR="${HOME}/.claude/logs"
LOG_FILE="${LOG_DIR}/tool-failures.jsonl"

mkdir -p "$LOG_DIR" 2> /dev/null || exit 0

# Read the hook payload from stdin (the harness passes a JSON object).
# If stdin is empty or non-JSON, fall back to recording just a timestamp.
PAYLOAD=$(cat 2> /dev/null || true)
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

if [ -n "$PAYLOAD" ]; then
  # Wrap the payload with our timestamp. Use python for safe JSON merge if available.
  if command -v python3 > /dev/null 2>&1; then
    printf '%s' "$PAYLOAD" | python3 -c "
import json, sys, os
try:
    data = json.loads(sys.stdin.read())
except Exception:
    data = {'raw': sys.stdin.read() if False else ''}
data['_logged_at'] = os.environ.get('TS', '')
print(json.dumps(data, separators=(',', ':')))
" TS="$TIMESTAMP" >> "$LOG_FILE" 2> /dev/null || \
      printf '{"_logged_at":"%s","raw":%s}\n' "$TIMESTAMP" "$(printf '%s' "$PAYLOAD" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))')" >> "$LOG_FILE"
  else
    # No python: log timestamp + raw payload as a single line (escape newlines)
    PAYLOAD_ESCAPED=$(printf '%s' "$PAYLOAD" | tr '\n' ' ')
    printf '{"_logged_at":"%s","raw":"%s"}\n' "$TIMESTAMP" "$PAYLOAD_ESCAPED" >> "$LOG_FILE"
  fi
else
  printf '{"_logged_at":"%s"}\n' "$TIMESTAMP" >> "$LOG_FILE"
fi

exit 0
