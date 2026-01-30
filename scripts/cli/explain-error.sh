#!/bin/bash
# Pipe error output to Claude for explanation
#
# Usage: some-command 2>&1 | explain-error.sh
#
# Reads from stdin and asks Claude to explain the error and suggest a fix.

set -e

if ! command -v claude &> /dev/null; then
  echo "Error: Claude Code CLI not found. Install from https://claude.ai/code"
  exit 1
fi

INPUT=$(cat)

if [ -z "$INPUT" ]; then
  echo "No input received. Usage: some-command 2>&1 | explain-error.sh"
  exit 1
fi

echo "$INPUT" | claude -p "Explain this error and suggest a fix. Be concise." \
  --max-turns 2
