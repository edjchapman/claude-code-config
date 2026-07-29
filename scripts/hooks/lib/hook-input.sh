# shellcheck shell=bash
# Shared stdin-payload helper for the hook scripts in scripts/hooks/.
# The harness delivers each hook's input as a JSON object on stdin (NOT via
# CLAUDE_* env vars). Source this from a sibling hook, then read fields off the
# payload you cat'd from stdin:
#
#   SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
#   . "$SCRIPT_DIR/lib/hook-input.sh"
#   PAYLOAD=$(cat 2> /dev/null || true)
#   file_path=$(hook_field "$PAYLOAD" tool_input.file_path)

# hook_field <payload> <dotted.key>
# Print the string value at the dotted key path in the JSON payload, or "" if
# the key is absent / non-string, the payload is unparseable, or python3 is
# unavailable. Callers layer their own env-var / positional fallbacks on top.
hook_field() {
  command -v python3 > /dev/null 2>&1 || return 0
  printf '%s' "$1" | HOOK_KEY="$2" python3 -c '
import json, os, sys
try:
    cur = json.load(sys.stdin)
except Exception:
    sys.exit(0)
for part in os.environ["HOOK_KEY"].split("."):
    cur = cur.get(part) if isinstance(cur, dict) else None
    if cur is None:
        break
print(cur if isinstance(cur, str) else "")
' 2> /dev/null
}
