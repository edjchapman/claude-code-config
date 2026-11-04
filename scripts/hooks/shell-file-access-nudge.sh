#!/usr/bin/env bash
# Nudge Claude back to Read/Edit/Write when a shell command reads or writes files in a way that skips path-scoped rules and edit hooks.
#
# Why: path-scoped rules load on a simple single-file `cat`/`head`/`sed -n`/`grep`,
# but not on `cd x && cat y`, a multi-file `cat`, or a script that writes a file
# (probed live on 2.1.318), and PostToolUse hooks such as format-on-edit match
# only Edit/Write. Auto mode encourages shell file access, so this is routine.
#
# Advisory only: it never blocks, because a shell rewrite is sometimes the right
# tool. Scratch paths are exempt since no project rule or formatter applies.

set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/hook-input.sh
. "$SCRIPT_DIR/lib/hook-input.sh"

PAYLOAD=$(cat 2> /dev/null || true)
CMD=$(hook_field "$PAYLOAD" tool_input.command)
[ -n "$CMD" ] || exit 0

matches() { printf '%s' "$CMD" | grep -Eq -- "$1"; }

matches '(^|[[:space:]"'\''=])(/private)?/(tmp|var/folders)/' && exit 0

READER='(cat|head|tail|sed -n)[[:space:]]'
SEPARATOR='(&&|;|\|\|)[[:space:]]*'

nudge=""
if matches '(^|[[:space:];&|])(sed -i|perl -[a-z]*i|cat[[:space:]]*>|tee[[:space:]])' \
  || { matches '(^|[[:space:];&|])python3?[[:space:]]' \
    && matches "write_text|write_bytes|open\([^)]*,[[:space:]]*(mode=)?[\"'][wax]b?[\"']"; }; then
  nudge="Use Edit/Write for repo files: this shell write skips path-scoped rules and format hooks."
elif matches "${SEPARATOR}${READER}" \
  || matches '(^|[[:space:];&|])(cat|head)[[:space:]]+[^-|;&<>[:space:]][^|;&<>[:space:]]*[[:space:]]+[^-|;&<>[:space:]]'; then
  nudge="Use Read, or one simple cat/sed -n with no cd prefix: compound and multi-file reads don't load path-scoped rules."
fi

[ -n "$nudge" ] || exit 0
printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","additionalContext":"%s"}}\n' "$nudge"
exit 0
