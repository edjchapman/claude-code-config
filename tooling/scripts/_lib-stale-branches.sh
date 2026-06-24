#!/usr/bin/env bash
# Shared classifier for local branch hygiene.
#
# Sourced by both `check-stale-branches.sh` (detection) and
# `sweep-stale-branches.sh` (destructive, bucket A only). Single source of
# truth: if one of those two scripts re-implemented classification, the
# destructive script could drift from the detection script — exactly the
# maintenance bug this tooling is designed to prevent.
#
# Side-effect-free: only `git for-each-ref`, `git rev-list`, `git rev-parse`,
# and `gh pr list` reads. No `git branch -D`, no `gh pr create`, no writes.
#
# Exports one function: `classify_branches`. It walks every local branch
# (except current + main), classifies each into one of 5 buckets, and prints
# one tab-separated record per branch to stdout:
#
#     <bucket>\t<branch-name>\t<context-blob>
#
# Buckets:
#
#   A — Safe to delete. ALL THREE positive signals required:
#         upstream tracking is `gone` AND
#         most recent PR has state == MERGED AND
#         mergedAt is a non-null ISO date.
#       Auto-deletable by sweep-stale-branches.sh with APPLY=1.
#
#   B — Closed unmerged, needs judgment. Most recent PR has state == CLOSED
#       and mergedAt is null. Never auto-deletable.
#
#   C — Ahead of origin/main, no PR ever existed. Never auto-deletable.
#
#   D — Orphaned / manual review. None of A/B/C/E apply (e.g. branch is
#       even with origin/main but has no PR, or origin/main missing so
#       ahead-count was inconclusive).
#
#   E — Unknown — GitHub lookup failed. `gh` exited non-zero, returned
#       malformed JSON, or any parse error. Critically distinct from B:
#       "lookup failed" is not the same signal as "PR closed unmerged",
#       and conflating them would confuse review of the output.
#
# Callers parse the bucket letter for decisions and pass the context blob
# through verbatim for display.
#
# Style: all branch names quoted everywhere; locals declared inside the
# function; no shellcheck warnings (run `shellcheck _lib-stale-branches.sh`
# before merging changes).

# Classify all local branches except current and `main`.
# Prints one tab-separated record per branch: bucket<TAB>name<TAB>context
classify_branches() {
  # Refresh origin's view before classifying. Without this, branches that
  # GitHub auto-deleted on merge linger as stale remote-tracking refs locally
  # (`origin/foo` present after `foo` is gone from GitHub), so the
  # upstream-gone signal misses them and they fall into bucket D ("manual
  # review") instead of bucket A ("auto-deletable"). Also refreshes
  # `origin/main` so bucket C's ahead-count uses current state.
  # Fail-soft: an offline run still classifies against locally-cached state,
  # matching the lib's WARN-only contract.
  git fetch --prune origin >/dev/null 2>&1 || true

  local current_branch
  current_branch=$(git symbolic-ref --quiet --short HEAD 2>/dev/null || echo "")

  # Pre-check origin/main availability — affects bucket C computation.
  local origin_main_ok=1
  if ! git rev-parse --verify --quiet origin/main >/dev/null 2>&1; then
    origin_main_ok=0
  fi

  # Walk every local branch with its upstream-tracking state.
  # Format: "<branch>\t<upstream-track-text>"
  # `upstream:track` produces strings like "[gone]", "[ahead 2]", "[behind 1]",
  # "[ahead 1, behind 2]", or "" when there is no upstream at all.
  local branches_raw
  branches_raw=$(git for-each-ref \
    --format='%(refname:short)%09%(upstream:track)' \
    refs/heads)

  local branch upstream_track
  while IFS=$'\t' read -r branch upstream_track; do
    [ -z "$branch" ] && continue
    [ "$branch" = "main" ] && continue
    [ "$branch" = "$current_branch" ] && continue

    classify_one "$branch" "$upstream_track" "$origin_main_ok"
  done <<< "$branches_raw"
}

# Classify a single branch. Args: <branch> <upstream-track-text> <origin-main-ok>
# Prints exactly one tab-separated record to stdout.
classify_one() {
  local branch="$1"
  local upstream_track="$2"
  local origin_main_ok="$3"

  local upstream_gone=0
  if [[ "$upstream_track" == *"gone"* ]]; then
    upstream_gone=1
  fi

  # Query GitHub for the most recent PR with this branch as head.
  # Strict JSON schema; any parse failure → bucket E.
  local pr_json gh_rc
  pr_json=$(gh pr list \
    --state all \
    --head "$branch" \
    --limit 1 \
    --json state,number,title,closedAt,mergedAt \
    2>/dev/null) && gh_rc=0 || gh_rc=$?

  if [ "$gh_rc" -ne 0 ]; then
    printf "E\t%s\tgh exited %d — network, auth, or rate-limit issue\n" \
      "$branch" "$gh_rc"
    return
  fi

  # Validate JSON is an array. Any jq failure → bucket E.
  if ! printf '%s' "$pr_json" | jq -e 'type == "array"' >/dev/null 2>&1; then
    printf "E\t%s\tgh returned malformed JSON\n" "$branch"
    return
  fi

  local pr_count
  pr_count=$(printf '%s' "$pr_json" | jq -r 'length' 2>/dev/null) || {
    printf "E\t%s\tjq parse error reading PR count\n" "$branch"
    return
  }

  if [ "$pr_count" = "0" ]; then
    # No PR ever existed for this branch. Possible buckets: C, D.
    classify_no_pr "$branch" "$origin_main_ok"
    return
  fi

  # Parse the PR record. Any field-extraction error → bucket E.
  # Extract all five fields in one jq call so a single failure → bucket E
  # cleanly (avoids the A&&B||C trap where the || only catches the last A).
  local pr_fields pr_state pr_number pr_title pr_closed_at pr_merged_at
  if ! pr_fields=$(printf '%s' "$pr_json" | jq -r '
        .[0] | [
          (.state // ""),
          (.number // ""),
          (.title // ""),
          (.closedAt // ""),
          (.mergedAt // "")
        ] | @tsv' 2>/dev/null); then
    printf "E\t%s\tjq parse error reading PR fields\n" "$branch"
    return
  fi
  IFS=$'\t' read -r pr_state pr_number pr_title pr_closed_at pr_merged_at \
    <<< "$pr_fields"

  # Bucket A: upstream gone + MERGED + mergedAt present. All three required.
  if [ "$upstream_gone" = "1" ] \
     && [ "$pr_state" = "MERGED" ] \
     && [ -n "$pr_merged_at" ] \
     && [ "$pr_merged_at" != "null" ]; then
    printf "A\t%s\tPR #%s merged %s\n" \
      "$branch" "$pr_number" "${pr_merged_at%T*}"
    return
  fi

  # Bucket B: PR closed without merging. Note: PR may be MERGED but upstream
  # not yet `gone` — that lands here as a precaution (we never auto-delete
  # without the gone signal). Display reflects actual PR state.
  if [ "$pr_state" = "CLOSED" ] \
     && { [ -z "$pr_merged_at" ] || [ "$pr_merged_at" = "null" ]; }; then
    printf "B\t%s\tPR #%s closed %s — %q\n" \
      "$branch" "$pr_number" "${pr_closed_at%T*}" "$pr_title"
    return
  fi

  # Anything else with a PR record (e.g. OPEN, or MERGED but upstream still
  # present) falls through to D so the human can decide.
  printf "D\t%s\tPR #%s state=%s, upstream-gone=%s — manual review\n" \
    "$branch" "$pr_number" "$pr_state" "$upstream_gone"
}

# Branch has no PR record. Classify into C (ahead-of-main) or D (everything else).
classify_no_pr() {
  local branch="$1"
  local origin_main_ok="$2"

  if [ "$origin_main_ok" = "0" ]; then
    printf "D\t%s\tno PR found; origin/main unavailable — manual review\n" \
      "$branch"
    return
  fi

  local ahead_count
  ahead_count=$(git rev-list --count "origin/main..$branch" 2>/dev/null) || {
    printf "D\t%s\tno PR found; rev-list failed — manual review\n" "$branch"
    return
  }

  if [ "$ahead_count" -gt 0 ]; then
    printf "C\t%s\t%s commit(s) ahead of origin/main, no PR\n" \
      "$branch" "$ahead_count"
  else
    printf "D\t%s\tno PR found; not ahead of origin/main — manual review\n" \
      "$branch"
  fi
}
