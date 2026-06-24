#!/usr/bin/env bash
# Surface stale local branches via 5-bucket classification.
#
# This is the detection layer for the local-branch-hygiene workflow,
# codifying the manual sweep performed on 2026-06-05 (20 stale branches
# cleared in one pass). Without this script, the same manual cross-
# referencing — upstream tracking state, `gh pr list --state all`, and
# judgment on closed-unmerged work — has to be redone by hand at every
# weekly cadence, and the judgment beat on bucket B/C gets skipped under
# fatigue.
#
# Sources scripts/_lib-stale-branches.sh as the single source of truth for
# classification — the sweep script sources the same lib, so they cannot
# drift.
#
# WARN-only — always exits 0, including on network failure, missing
# origin/main, or any other degraded state. Failure to look up PR state is
# information to surface (bucket E), not a hard error. This matches the
# convention of every other `check-*.sh` in the repo.
#
# Local-only and network-bound (gh + jq required). NOT wired into the
# default `make check` target — runnable via `make check-stale-branches`,
# typically as part of the weekly review rhythm.

set -euo pipefail
cd "$(dirname "$0")/.."

# Source the shared classifier. Exit 1 only if the lib is missing or
# unsourceable — that's a real "tooling broken" state, not a degraded run.
LIB="./scripts/_lib-stale-branches.sh"
if [ ! -f "$LIB" ]; then
  echo "error: $LIB not found — cannot classify branches" >&2
  exit 1
fi
# shellcheck disable=SC1090,SC1091  # dynamic source path; lib presence guarded above
. "$LIB"

# Run the classifier. Always succeeds (records are produced even for
# degraded buckets D/E).
records=$(classify_branches)

count_a=0; count_b=0; count_c=0; count_d=0; count_e=0
rows_a=""; rows_b=""; rows_c=""; rows_d=""; rows_e=""

if [ -n "$records" ]; then
  while IFS=$'\t' read -r bucket branch context; do
    [ -z "$bucket" ] && continue
    case "$bucket" in
      A) count_a=$((count_a + 1)); rows_a+=$(printf "  %s  (%s)\n" "$branch" "$context") ;;
      B) count_b=$((count_b + 1)); rows_b+=$(printf "  %s  (%s)\n" "$branch" "$context") ;;
      C) count_c=$((count_c + 1)); rows_c+=$(printf "  %s  (%s)\n" "$branch" "$context") ;;
      D) count_d=$((count_d + 1)); rows_d+=$(printf "  %s  (%s)\n" "$branch" "$context") ;;
      E) count_e=$((count_e + 1)); rows_e+=$(printf "  %s  (%s)\n" "$branch" "$context") ;;
    esac
    rows_a+=$'\n'; rows_b+=$'\n'; rows_c+=$'\n'; rows_d+=$'\n'; rows_e+=$'\n'
  done <<< "$records"
fi

total=$((count_a + count_b + count_c + count_d + count_e))

if [ "$total" -eq 0 ]; then
  echo "OK: no stale local branches (only 'main' and current branch present, or all branches are tracked + open)"
  exit 0
fi

if [ "$count_a" -gt 0 ]; then
  printf "=== Bucket A — Safe to delete (%d) ===\n" "$count_a"
  printf "%s" "$rows_a"
  echo
fi

if [ "$count_b" -gt 0 ]; then
  printf "=== Bucket B — Closed unmerged, needs judgment (%d) ===\n" "$count_b"
  printf "%s" "$rows_b"
  echo "  → If superseded by later work, delete with: git branch -D <name>"
  echo "  → If still relevant, re-open the PR or rebase onto current main"
  echo
fi

if [ "$count_c" -gt 0 ]; then
  printf "=== Bucket C — Ahead of main, no PR (%d) ===\n" "$count_c"
  printf "%s" "$rows_c"
  echo "  → Consider: gh pr create  (or delete if abandoned)"
  echo
fi

if [ "$count_d" -gt 0 ]; then
  printf "=== Bucket D — Orphaned / manual review (%d) ===\n" "$count_d"
  printf "%s" "$rows_d"
  echo
fi

if [ "$count_e" -gt 0 ]; then
  printf "=== Bucket E — Unknown, GitHub lookup failed (%d) ===\n" "$count_e"
  printf "%s" "$rows_e"
  echo "  → Re-run when GitHub is reachable; do not delete without classification"
  echo
fi

printf "Summary: A=%d  B=%d  C=%d  D=%d  E=%d\n" \
  "$count_a" "$count_b" "$count_c" "$count_d" "$count_e"

if [ "$count_a" -gt 0 ]; then
  echo "Run 'make sweep-branches APPLY=1' to delete bucket A (other buckets require manual review)."
fi

exit 0
