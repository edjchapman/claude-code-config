#!/usr/bin/env bash
# Run the project's check command before Claude finishes, and send failures back as a blocked stop.
#
# Why: "verify before claiming done" written as an instruction gets skipped under
# pressure; a Stop hook makes it mechanical. Opt-in per project: a repo enables it
# by committing `.claude/stop-check`, whose first non-comment line is a fast,
# read-only check command (e.g. `make check`). Formatters don't belong there,
# because they rewrite files.
#
# To stay cheap it re-runs only when the working tree changed since the last pass,
# and it treats a clean tree on the session's first stop as already verified
# (pre-commit gated it). It never re-blocks a tree it already reported, so Claude
# can decline an unrelated failure by explaining it. After MAX_BLOCKS failing
# edit-and-retry rounds it lets the stop through with a warning, so a check
# Claude can't fix never traps the session.
# Set CLAUDE_STOP_CHECK=0 to disable it for a session.

set -u

MAX_BLOCKS=${CLAUDE_STOP_CHECK_MAX_BLOCKS:-3}

[ "${CLAUDE_STOP_CHECK:-1}" = "0" ] && exit 0
command -v python3 > /dev/null 2>&1 || exit 0
command -v git > /dev/null 2>&1 || exit 0

PAYLOAD=$(cat 2> /dev/null || true)
fields=$(printf '%s' "$PAYLOAD" | python3 -c '
import json, sys
try:
    d = json.load(sys.stdin)
except Exception:
    d = {}
print(d.get("cwd") or "")
print(d.get("session_id") or "nosession")
' 2> /dev/null) || exit 0
CWD=$(printf '%s\n' "$fields" | sed -n 1p)
SESSION=$(printf '%s\n' "$fields" | sed -n 2p | tr -c 'A-Za-z0-9_-' '_')
[ -n "$CWD" ] || CWD=$PWD

ROOT=$(git -C "$CWD" rev-parse --show-toplevel 2> /dev/null) || exit 0
CONFIG="$ROOT/.claude/stop-check"
[ -f "$CONFIG" ] || exit 0
CHECK=$(grep -Ev '^[[:space:]]*(#|$)' "$CONFIG" | head -1)
[ -n "$CHECK" ] || exit 0

STATE_DIR="${TMPDIR:-/tmp}/claude-stop-check/$SESSION"
mkdir -p "$STATE_DIR" 2> /dev/null || exit 0
KEY=$(printf '%s' "$ROOT" | shasum | cut -c1-12)
PASS_FILE="$STATE_DIR/$KEY.pass"
BLOCKS_FILE="$STATE_DIR/$KEY.blocks"
FAIL_FILE="$STATE_DIR/$KEY.fail"

# Untracked files are hashed by content so a new file's edits also count.
fingerprint() {
  {
    git -C "$ROOT" rev-parse HEAD 2> /dev/null
    git -C "$ROOT" diff HEAD 2> /dev/null
    git -C "$ROOT" ls-files --others --exclude-standard -z 2> /dev/null \
      | (cd "$ROOT" && xargs -0 shasum 2> /dev/null)
  } | shasum | cut -c1-40
}

FP=$(fingerprint)

if [ ! -f "$PASS_FILE" ] && [ -z "$(git -C "$ROOT" status --porcelain 2> /dev/null)" ]; then
  printf '%s\n' "$FP" > "$PASS_FILE"
  exit 0
fi
[ -f "$PASS_FILE" ] && [ "$(cat "$PASS_FILE")" = "$FP" ] && exit 0
# Already reported this exact tree: Claude chose not to change anything, so re-blocking adds nothing.
[ -f "$FAIL_FILE" ] && [ "$(cat "$FAIL_FILE")" = "$FP" ] && exit 0

OUTPUT=$(cd "$ROOT" && bash -c "$CHECK" 2>&1)
STATUS=$?

if [ "$STATUS" -eq 0 ]; then
  printf '%s\n' "$FP" > "$PASS_FILE"
  rm -f "$BLOCKS_FILE" "$FAIL_FILE"
  exit 0
fi

BLOCKS=$(($(cat "$BLOCKS_FILE" 2> /dev/null || echo 0) + 1))
printf '%s\n' "$BLOCKS" > "$BLOCKS_FILE"
printf '%s\n' "$FP" > "$FAIL_FILE"

TAIL=$(printf '%s\n' "$OUTPUT" | tail -40)
if [ "$BLOCKS" -gt "$MAX_BLOCKS" ]; then
  rm -f "$BLOCKS_FILE"
  CHECK="$CHECK" BLOCKS="$MAX_BLOCKS" python3 -c '
import json, os
print(json.dumps({"systemMessage": f"stop-check: `{os.environ["CHECK"]}` is still failing after {os.environ["BLOCKS"]} attempts; letting the stop through. Run it yourself before trusting this turn."}))
'
  exit 0
fi

CHECK="$CHECK" TAIL="$TAIL" STATUS="$STATUS" python3 -c '
import json, os
reason = (
    f"The project check `{os.environ["CHECK"]}` failed (exit {os.environ["STATUS"]}) after your changes. "
    "Fix the cause, or if the failure is unrelated to this task, say so explicitly in your reply. "
    "Last lines of output:\n\n" + os.environ["TAIL"]
)
print(json.dumps({"decision": "block", "reason": reason}))
'
exit 0
