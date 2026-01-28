#!/bin/bash
# Preserve working state before context compaction
# Used by: PreCompact hook in settings.json
#
# Outputs key state information so Claude retains it after compaction

# Only run in a git repository
if ! git rev-parse --is-inside-work-tree &>/dev/null; then
    exit 0
fi

echo "=== Pre-Compact State Snapshot ==="
echo ""

# Current branch
echo "Branch: $(git branch --show-current 2>/dev/null || echo 'detached HEAD')"
echo ""

# Staged files
STAGED=$(git diff --cached --name-only 2>/dev/null)
if [ -n "$STAGED" ]; then
    echo "Staged files:"
    echo "$STAGED"
    echo ""
fi

# Modified files
MODIFIED=$(git diff --name-only 2>/dev/null)
if [ -n "$MODIFIED" ]; then
    echo "Modified (unstaged) files:"
    echo "$MODIFIED"
    echo ""
fi

# Untracked files
UNTRACKED=$(git ls-files --others --exclude-standard 2>/dev/null | head -10)
if [ -n "$UNTRACKED" ]; then
    echo "Untracked files (first 10):"
    echo "$UNTRACKED"
    echo ""
fi

# Recent commits on this branch
echo "Recent commits (last 5):"
git log --oneline -5 2>/dev/null
echo ""

echo "=== End State Snapshot ==="
