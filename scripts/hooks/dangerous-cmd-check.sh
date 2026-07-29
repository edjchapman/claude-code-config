#!/usr/bin/env bash
# Defense-in-depth: block obviously catastrophic command patterns before they run.
# Used by: PreToolUse (Bash) hook in settings.json
#
# The harness passes the hook payload as JSON on stdin; the command is at
# .tool_input.command. (The older $CLAUDE_TOOL_INPUT env var is NOT set by the
# harness.) Exit 0 = allow, Exit 2 = block. The block reason MUST go to STDERR —
# the harness surfaces stderr on a blocking exit, not stdout.
#
# This is a best-effort SECONDARY guard, not a security boundary. It normalises
# whitespace and matches case-insensitively, but it is still bypassable (via
# variables, quoting, encodings, etc.). The primary protections are the settings
# deny-lists and simply not allow-listing catastrophic commands.

set -u

PAYLOAD=$(cat 2> /dev/null || true)

# Extract the actual command string from the JSON payload.
CMD=""
if [ -n "$PAYLOAD" ] && command -v python3 > /dev/null 2>&1; then
  CMD=$(printf '%s' "$PAYLOAD" | python3 -c '
import json, sys
try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)
ti = data.get("tool_input") or {}
print(ti.get("command") or "")
' 2> /dev/null)
fi
# Fallbacks: legacy env var, or treat raw stdin as the command.
CMD="${CMD:-${CLAUDE_TOOL_INPUT:-$PAYLOAD}}"
[ -n "$CMD" ] || exit 0

# Collapse runs of whitespace so "rm  -rf" and "rm -rf" match identically.
NORM=$(printf '%s' "$CMD" | tr -s '[:space:]' ' ')

block() {
  echo "BLOCKED: dangerous command pattern detected ($1)" >&2
  exit 2
}
check() { printf '%s' "$NORM" | grep -Eiq "$1" && block "$2"; }

# Extended-regex patterns, matched case-insensitively against the normalised
# command. Root/home/system-dir deletes are ANCHORED so legitimate sub-path
# deletes ("rm -rf /tmp/build", "rm -rf /var/tmp/x", "rm -rf ~/project/dist")
# are NOT blocked, while wiping a system dir itself (or its glob) IS.
check 'rm +-[a-z]*r[a-z]* +/( |$|\*)'                'rm -rf /'
check 'rm +-[a-z]*r[a-z]* +/(etc|usr|bin|sbin|lib64|lib|var|boot|sys|proc|dev|root|opt)($| |/\*?$)' 'rm -rf a system dir'
check 'rm +-[a-z]*r[a-z]* +(~|\$\{?HOME\}?)( |/?$)'  'rm -rf $HOME'
check 'rm +.*--no-preserve-root'                     'rm --no-preserve-root'
check 'dd +if=/dev/'                                 'dd if=/dev/...'
check 'mkfs\.'                                       'mkfs.*'
check 'chmod +-R +777'                               'chmod -R 777'
check '> +/dev/sd[a-z]'                              '> /dev/sd*'
check ':\(\) *\{.*\|.*&.*\}'                         'fork bomb'
check 'mv +/ '                                       'mv / ...'
check 'sudo +rm '                                    'sudo rm'
check 'sudo +mv '                                    'sudo mv'
check '(wget|curl)[^|]*\| *(sh|bash)'                'pipe-to-shell (curl|wget | sh)'

exit 0
