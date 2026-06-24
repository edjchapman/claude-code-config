#!/usr/bin/env bash
# Delete local branches classified as bucket A (safe to delete).
#
# Destructive — but tightly gated. Sources the same
# scripts/_lib-stale-branches.sh as the detection script, so the bucket-A
# discipline is the ONLY decision-maker. Three positive signals required
# for bucket A (upstream tracking is `gone`, PR state is MERGED, mergedAt
# is non-null); anything missing demotes to a non-deletable bucket.
#
# Dry-run by default. Set APPLY=1 (or pass --apply) to actually delete.
#
# Exit codes:
#   0  — successful dry run, OR successful delete pass, OR there were no
#        bucket-A branches to delete.
#   1  — real safety failure: current branch is in bucket A and APPLY=1 was
#        set (refuse), OR a `git branch -D` call itself failed, OR the
#        classifier lib is unsourceable.
#
# Network/auth degradation never raises an error — bucket A is empty in that
# case, which is the correct conservative behaviour.

set -euo pipefail
cd "$(dirname "$0")/.."

LIB="./scripts/_lib-stale-branches.sh"
if [ ! -f "$LIB" ]; then
  echo "error: $LIB not found — cannot classify branches" >&2
  exit 1
fi
# shellcheck disable=SC1090,SC1091  # dynamic source path; lib presence guarded above
. "$LIB"

# Parse --apply flag (equivalent to APPLY=1).
APPLY="${APPLY:-0}"
for arg in "$@"; do
  case "$arg" in
    --apply) APPLY=1 ;;
    *) echo "error: unknown argument: $arg" >&2; exit 1 ;;
  esac
done

current_branch=$(git symbolic-ref --quiet --short HEAD 2>/dev/null || echo "")

# Collect bucket-A records only.
bucket_a=""
while IFS=$'\t' read -r bucket branch context; do
  [ "$bucket" = "A" ] || continue
  bucket_a+=$(printf "%s\t%s\n" "$branch" "$context")
  bucket_a+=$'\n'
done <<< "$(classify_branches)"

if [ -z "$bucket_a" ]; then
  echo "OK: no bucket-A branches to sweep"
  exit 0
fi

# Safety guard: refuse to delete current branch when actually applying.
if [ "$APPLY" = "1" ]; then
  while IFS=$'\t' read -r branch _context; do
    [ -z "$branch" ] && continue
    if [ "$branch" = "$current_branch" ]; then
      printf 'error: refusing to delete current branch "%s" — checkout main first\n' \
        "$current_branch" >&2
      exit 1
    fi
  done <<< "$bucket_a"
fi

if [ "$APPLY" != "1" ]; then
  echo "DRY RUN — no branches deleted. Re-run with APPLY=1 (or --apply) to delete:"
  while IFS=$'\t' read -r branch context; do
    [ -z "$branch" ] && continue
    printf "  would delete: %s  (%s)\n" "$branch" "$context"
  done <<< "$bucket_a"
  exit 0
fi

echo "Deleting bucket-A branches:"
deleted=0
while IFS=$'\t' read -r branch context; do
  [ -z "$branch" ] && continue
  # Quote branch name everywhere. `git branch -D` failure is a real error.
  if ! git branch -D "$branch" >/dev/null 2>&1; then
    printf 'error: git branch -D "%s" failed — working tree may be in unexpected state\n' \
      "$branch" >&2
    exit 1
  fi
  printf "  deleted: %s  (%s)\n" "$branch" "$context"
  deleted=$((deleted + 1))
done <<< "$bucket_a"

printf "Done — %d branch(es) deleted.\n" "$deleted"
exit 0
