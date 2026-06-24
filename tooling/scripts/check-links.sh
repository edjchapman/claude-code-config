#!/usr/bin/env bash
# Check that internal markdown links resolve to existing files.
# Excludes http/mailto/tel links and template placeholder files.
#
# Run via `make check-links`. Wired into `make check` (hard-fail).

set -uo pipefail
cd "$(dirname "$0")/.." || exit 1

tmpfile=$(mktemp)
trap 'rm -f "$tmpfile"' EXIT

while IFS= read -r file; do
  dir=$(dirname "$file")
  grep -oE '\[[^]]*\]\([^)]+\)' "$file" 2>/dev/null \
    | sed 's/.*(\(.*\))/\1/' \
    | sed 's/#.*//' \
    | grep -v '^$' \
    | grep -v '^http' \
    | grep -v '^mailto:' \
    | grep -v '^tel:' \
    | while read -r link; do
      target="$dir/$link"
      if [ ! -e "$target" ]; then
        echo "FAIL: broken link in $file -> $link"
        echo 1 > "$tmpfile"
      fi
    done
done < <(find . -name '*.md' \
  -not -path './.git/*' \
  -not -path './.idea/*' \
  -not -path './.claude/*' \
  -not -path './.junie/*' \
  -not -path '*/_templates/*')

if [ -s "$tmpfile" ]; then
  exit 1
fi

echo "OK: all internal links resolve"
exit 0
