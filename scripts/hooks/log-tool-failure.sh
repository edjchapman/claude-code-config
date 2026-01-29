#!/bin/bash
# Log tool failures for debugging
# Reads tool failure JSON from stdin, appends to debug log

LOG_DIR="$HOME/.claude/debug"
LOG_FILE="$LOG_DIR/tool-failures.log"

mkdir -p "$LOG_DIR"

# Read JSON from stdin
INPUT=$(cat)

if [ -z "$INPUT" ]; then
  exit 0
fi

TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
TOOL_NAME=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_name','unknown'))" 2> /dev/null || echo "unknown")
ERROR=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('error','no error message'))" 2> /dev/null || echo "parse error")

echo "[$TIMESTAMP] tool=$TOOL_NAME error=$ERROR" >> "$LOG_FILE"
