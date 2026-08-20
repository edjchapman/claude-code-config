#!/usr/bin/env bash
# Preserve working state before context compaction
#
# Why: a hook's plain stdout is NOT injected for PreCompact (only
# UserPromptSubmit / UserPromptExpansion / SessionStart inject stdout), so the
# snapshot goes to a session-keyed file that post-compact-restore.sh re-injects
# via hookSpecificOutput.additionalContext once compaction completes.

set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/git-context.sh
. "$SCRIPT_DIR/lib/git-context.sh"
# shellcheck source=lib/hook-input.sh
. "$SCRIPT_DIR/lib/hook-input.sh"

# Only run in a git repository
if ! in_git_work_tree; then
  exit 0
fi

# Session id from the stdin payload keys the state file so the matching
# PostCompact restore picks up this session's snapshot (not another session's).
PAYLOAD=$(cat 2> /dev/null || true)
SESSION_ID=$(hook_field "$PAYLOAD" session_id)
SESSION_ID="${SESSION_ID:-default}"

CACHE_DIR="${HOME}/.claude/cache"
mkdir -p "$CACHE_DIR" 2> /dev/null || exit 0
STATE_FILE="${CACHE_DIR}/precompact-${SESSION_ID}.md"

{
  echo "=== Pre-Compact State Snapshot ==="
  echo ""
  echo "Branch: $(git_branch)"
  echo ""

  STAGED=$(git diff --cached --name-only 2> /dev/null)
  if [ -n "$STAGED" ]; then
    echo "Staged files:"
    echo "$STAGED"
    echo ""
  fi

  MODIFIED=$(git diff --name-only 2> /dev/null)
  if [ -n "$MODIFIED" ]; then
    echo "Modified (unstaged) files:"
    echo "$MODIFIED"
    echo ""
  fi

  UNTRACKED=$(git ls-files --others --exclude-standard 2> /dev/null | head -10)
  if [ -n "$UNTRACKED" ]; then
    echo "Untracked files (first 10):"
    echo "$UNTRACKED"
    echo ""
  fi

  echo "Recent commits (last 5):"
  git log --oneline -5 2> /dev/null
  echo ""
  echo "=== End State Snapshot ==="
} > "$STATE_FILE" 2> /dev/null

exit 0
