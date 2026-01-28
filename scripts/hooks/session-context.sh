#!/bin/bash
# Output git context at session start so Claude has immediate awareness
# Used by: SessionStart hook in settings.json

# Only run in a git repository
if ! git rev-parse --is-inside-work-tree &> /dev/null; then
  exit 0
fi

echo "=== Session Context ==="
echo ""

# Current branch
echo "Branch: $(git branch --show-current 2> /dev/null || echo 'detached HEAD')"
echo ""

# Recent commits (last 5)
echo "Recent commits:"
git log --oneline -5 2> /dev/null || echo "  (no commits)"
echo ""

# Dirty files
DIRTY=$(git status --porcelain 2> /dev/null)
if [ -n "$DIRTY" ]; then
  echo "Uncommitted changes:"
  echo "$DIRTY" | head -20
  TOTAL=$(echo "$DIRTY" | wc -l | tr -d ' ')
  if [ "$TOTAL" -gt 20 ]; then
    echo "  ... and $((TOTAL - 20)) more files"
  fi
else
  echo "Working tree: clean"
fi

echo ""
echo "=== End Context ==="
