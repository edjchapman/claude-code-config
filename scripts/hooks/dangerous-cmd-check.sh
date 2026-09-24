#!/usr/bin/env bash
# Defense-in-depth: block obviously catastrophic command patterns before they run.
#
# Why: a best-effort SECONDARY guard, not a security boundary — it stays
# bypassable via variables, quoting and encodings, so the primary protections
# remain the settings deny-lists and simply not allow-listing catastrophic
# commands.
#
# The harness passes the hook payload as JSON on stdin; the command is at
# .tool_input.command. (The older $CLAUDE_TOOL_INPUT env var is NOT set by the
# harness.) Exit 0 = allow, Exit 2 = block. The block reason MUST go to STDERR —
# the harness surfaces stderr on a blocking exit, not stdout.
#
# Matching normalises whitespace, ignores case, and skips heredoc bodies that
# are data rather than code (see strip_heredoc_bodies below). Quoted arguments
# are still matched, so `bash -c "rm -rf /"` is blocked.

set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/hook-input.sh
. "$SCRIPT_DIR/lib/hook-input.sh"

PAYLOAD=$(cat 2> /dev/null || true)
# Extract the command string; fall back to the legacy env var or raw stdin.
CMD=$(hook_field "$PAYLOAD" tool_input.command)
CMD="${CMD:-${CLAUDE_TOOL_INPUT:-$PAYLOAD}}"
[ -n "$CMD" ] || exit 0

# A heredoc body is stdin DATA for the program receiving it, not shell code, so
# matching against it reports commands that never run — writing a file whose
# CONTENT documents a dangerous pattern was blocked, and this repo ships deny
# rules containing exactly those strings.
#
# Exception: when the heredoc feeds a shell the body IS executed, so it stays in
# scope; stripping it unconditionally would be a one-line bypass.
strip_heredoc_bodies() {
  awk '
    function feeds_a_shell(line) {
      return (line ~ /(^|[ \t;&|(])([^ \t]*\/)?(ba|z|k|da)?sh([ \t]|$)/)
    }
    BEGIN { in_body = 0; strip = 0; term = "" }
    {
      if (in_body) {
        trimmed = $0
        sub(/^[ \t]+/, "", trimmed)          # <<- allows a tab-indented terminator
        if (trimmed == term) { in_body = 0; next }
        if (!strip) { print }
        next
      }
      print
      if (match($0, /<<-?[ \t]*["\047]?[A-Za-z_][A-Za-z0-9_]*["\047]?/)) {
        term = substr($0, RSTART, RLENGTH)
        sub(/^<<-?[ \t]*/, "", term)
        gsub(/["\047]/, "", term)
        strip = feeds_a_shell($0) ? 0 : 1
        in_body = 1
      }
    }
  '
}

# Collapse runs of whitespace so "rm  -rf" and "rm -rf" match identically.
NORM=$(printf '%s' "$CMD" | strip_heredoc_bodies | tr -s '[:space:]' ' ')

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
