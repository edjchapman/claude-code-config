#!/bin/bash
# Review uncommitted changes using Claude headless mode
#
# Usage: review-changes.sh
#
# Reviews staged and unstaged changes for bugs, security issues, and code quality.

set -e

if ! command -v claude &> /dev/null; then
  echo "Error: Claude Code CLI not found. Install from https://claude.ai/code"
  exit 1
fi

if git rev-parse HEAD &> /dev/null; then
  DIFF=$(git diff HEAD 2> /dev/null)
else
  DIFF=$(git diff --cached 2> /dev/null)
fi

if [ -z "$DIFF" ]; then
  echo "No changes to review."
  exit 0
fi

echo "$DIFF" | claude -p "Review these changes for bugs, security issues, and code quality. Be concise." \
  --allowedTools "Read" \
  --max-turns 3 \
  --output-format stream-json
