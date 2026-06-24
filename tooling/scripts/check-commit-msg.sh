#!/usr/bin/env bash
# Validate a commit subject against the Conventional Commits standard.
#
# Closes the commit "type" vocabulary to a Conventional Commits grammar with a
# fixed set (edit TYPES below to taste):
#
#     <type>[(<scope>)][!]: <subject>
#
#   type   required, lowercase, from the closed set below
#   scope  optional, lowercase slug — a sub-area, e.g. build(makefile);
#          regex [a-z0-9][a-z0-9-]*
#   !      optional, marks a breaking change
#   subject  required free text
#
# WHERE IT RUNS
#   - .githooks/commit-msg passes the commit message FILE as $1 (local).
#   - .github/workflows/commit-style.yml pipes the PR TITLE via --stdin (CI).
#     When you squash-merge, the PR title becomes the permanent commit subject —
#     so that is the thing worth validating. Per-branch WIP commits are not
#     range-validated; they are squashed away.
#
# WARN-ONLY FIRST
#   Default behaviour prints a WARN: line and exits 0, matching the repo's
#   incremental-validation pattern (new checks ship warn-only, harden after an
#   adjustment runway). Pass --strict to turn a non-conforming subject into a
#   hard failure (exit 1). PROMOTION TODO: once commits have followed the
#   standard for a few weeks, add --strict to both the commit-msg hook and the
#   commit-style CI workflow to make it blocking.
#
# USAGE
#   ./scripts/check-commit-msg.sh <commit-msg-file>     # hook mode
#   printf '%s\n' "$SUBJECT" | ./scripts/check-commit-msg.sh --stdin
#   ./scripts/check-commit-msg.sh --stdin --strict      # hard-fail mode

set -euo pipefail

TYPES='feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert'
SUBJECT_RE="^(${TYPES})(\([a-z0-9][a-z0-9-]*\))?!?: .+"
MAX_LEN=72

strict=0
src=""
for arg in "$@"; do
  case "$arg" in
    --strict) strict=1 ;;
    --stdin)  src="-" ;;
    -h|--help)
      grep '^#' "$0" | sed 's/^# \{0,1\}//'
      exit 0
      ;;
    *) src="$arg" ;;
  esac
done
[ -z "$src" ] && src="-"  # default to stdin when no source given

# Read only the first line — the subject — from stdin or the message file.
if [ "$src" = "-" ]; then
  IFS= read -r subject || subject=""
else
  if [ ! -f "$src" ]; then
    echo "check-commit-msg: message file not found: $src" >&2
    exit 2
  fi
  subject=$(head -n 1 "$src")
fi

# Skip auto-generated / non-subject lines that never need to conform.
case "$subject" in
  ""|"Merge "*|"fixup! "*|"squash! "*|"Revert \""*)
    exit 0
    ;;
esac

if printf '%s' "$subject" | grep -Eq "$SUBJECT_RE"; then
  # Conforms. Length is advisory only — warn but never fail, even in --strict.
  if [ "${#subject}" -gt "$MAX_LEN" ]; then
    echo "WARN: commit subject is ${#subject} chars (>${MAX_LEN}); consider tightening."
  fi
  echo "OK: commit subject follows the commit standard."
  exit 0
fi

echo "WARN: commit subject does not follow the Conventional Commits standard."
echo "  Subject:  \"${subject}\""
echo "  Expected: <type>[(<scope>)][!]: <subject>   e.g. feat(api): …  ·  fix: …  ·  ci: …"
echo "  Types:    ${TYPES//|/ }"
echo "  See https://www.conventionalcommits.org/ for the full standard."
if [ "$strict" -eq 1 ]; then
  exit 1
fi
exit 0
