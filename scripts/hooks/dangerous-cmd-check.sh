#!/bin/bash
# Defense-in-depth: block dangerous command patterns before execution
# Used by: PreToolUse (Bash) hook in settings.json
#
# Expects the command to check via $CLAUDE_TOOL_INPUT or stdin
# Exit 0 = allow, Exit 2 = block

CMD="${CLAUDE_TOOL_INPUT:-$(cat)}"

# Literal patterns matched with grep -qF (fixed string)
FIXED_PATTERNS=(
  "rm -rf /"
  "rm -rf /*"
  "rm -rf ~"
  "rm -rf ~/"
  'rm -rf $HOME'
  'rm -rf ${HOME}'
  "dd if=/dev/"
  "mkfs."
  "chmod -R 777 /"
  "> /dev/sda"
  ":(){ :|:& };:"
  "mv / "
)

# Regex patterns matched with grep -qE (extended regex)
REGEX_PATTERNS=(
  "wget.*\|.*sh"
  "curl.*\|.*sh"
  "curl.*\|.*bash"
  "wget.*\|.*bash"
)

for pattern in "${FIXED_PATTERNS[@]}"; do
  if echo "$CMD" | grep -qF "$pattern"; then
    echo "BLOCKED: Dangerous command pattern detected: $pattern"
    exit 2
  fi
done

for pattern in "${REGEX_PATTERNS[@]}"; do
  if echo "$CMD" | grep -qE "$pattern"; then
    echo "BLOCKED: Dangerous command pattern detected: $pattern"
    exit 2
  fi
done

exit 0
