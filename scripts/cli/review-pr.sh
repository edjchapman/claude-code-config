#!/bin/bash
# Headless PR review
#
# Usage: review-pr.sh <pr-number>
#
# Reviews a pull request for bugs, security issues, and test coverage.

set -e

PR_NUM="${1:?Usage: review-pr.sh <pr-number>}"

if ! command -v claude &> /dev/null; then
  echo "Error: Claude Code CLI not found. Install from https://claude.ai/code"
  exit 1
fi

claude -p "Review PR #$PR_NUM. Focus on bugs, security, and test coverage." \
  --allowedTools "Bash(gh pr *),Bash(gh api *),Read" \
  --max-turns 10
