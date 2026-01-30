#!/bin/bash

# @raycast.schemaVersion 1
# @raycast.title Review Changes
# @raycast.mode fullOutput
# @raycast.packageName Claude Code
# @raycast.icon 🤖
# @raycast.description Review uncommitted git changes with Claude Code

cd "$(pwd)" || exit 1

if ! command -v claude &> /dev/null; then
  echo "Error: Claude Code CLI not found"
  exit 1
fi

~/claude-code-config/scripts/cli/review-changes.sh
