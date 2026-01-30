#!/bin/bash
# Summarize yesterday's git activity across all projects
#
# Usage: daily-report.sh
#
# Generates a summary of git commits, files changed, and open PRs from the last 24 hours.

set -e

if ! command -v claude &> /dev/null; then
  echo "Error: Claude Code CLI not found. Install from https://claude.ai/code"
  exit 1
fi

claude -p "Summarize my git activity from the last 24 hours. List commits, files changed, and any open PRs." \
  --allowedTools "Bash(git log *),Bash(gh pr list *)" \
  --max-turns 5
