# shellcheck shell=bash
# Shared git-context helpers for the hook scripts in scripts/hooks/.
# Not a hook itself — source it from a sibling script:
#
#   SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
#   . "$SCRIPT_DIR/lib/git-context.sh"

# True when the current directory is inside a git work tree.
in_git_work_tree() {
  git rev-parse --is-inside-work-tree > /dev/null 2>&1
}

# Current branch name; falls back to the short SHA on a detached HEAD,
# then to "$1" (default "no-git") outside a repository.
git_branch() {
  git symbolic-ref --short HEAD 2> /dev/null \
    || git rev-parse --short HEAD 2> /dev/null \
    || echo "${1:-no-git}"
}

# Number of dirty (staged, unstaged, or untracked) files.
git_dirty_count() {
  git status --porcelain 2> /dev/null | wc -l | tr -d ' '
}
