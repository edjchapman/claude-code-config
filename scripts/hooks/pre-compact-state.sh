#!/usr/bin/env bash
# Preserve working state before context compaction
# Used by: PreCompact hook in settings.json
#
# Outputs key state information so Claude retains it after compaction

set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/git-context.sh
. "$SCRIPT_DIR/lib/git-context.sh"

# Only run in a git repository
if ! in_git_work_tree; then
  exit 0
fi

echo "=== Pre-Compact State Snapshot ==="
echo ""

# Current branch
echo "Branch: $(git_branch)"
echo ""

# Staged files
STAGED=$(git diff --cached --name-only 2> /dev/null)
if [ -n "$STAGED" ]; then
  echo "Staged files:"
  echo "$STAGED"
  echo ""
fi

# Modified files
MODIFIED=$(git diff --name-only 2> /dev/null)
if [ -n "$MODIFIED" ]; then
  echo "Modified (unstaged) files:"
  echo "$MODIFIED"
  echo ""
fi

# Untracked files
UNTRACKED=$(git ls-files --others --exclude-standard 2> /dev/null | head -10)
if [ -n "$UNTRACKED" ]; then
  echo "Untracked files (first 10):"
  echo "$UNTRACKED"
  echo ""
fi

# Recent commits on this branch
echo "Recent commits (last 5):"
git log --oneline -5 2> /dev/null
echo ""

echo "=== End State Snapshot ==="
