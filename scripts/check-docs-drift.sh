#!/usr/bin/env bash
# check-docs-drift.sh
#
# Fail CI if a primitive on disk isn't mentioned in CLAUDE.md or README.md.
# Catches the kind of drift where someone adds a new skill / agent / command /
# hook but forgets to document it. Both docs are searched together — either is
# sufficient mention; we only fail if neither references the file.
#
# Run from repo root: scripts/check-docs-drift.sh

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

docs=(CLAUDE.md README.md)
fail=0

check_dir() {
    local dir="$1" ext="$2" label="$3"
    [ -d "$dir" ] || return 0
    for f in "$dir"/*."$ext"; do
        [ -e "$f" ] || continue
        local name
        name="$(basename "$f" ."$ext")"
        if ! grep -q -F "$name" "${docs[@]}"; then
            echo "DRIFT: $label '$name' (from $f) is not mentioned in CLAUDE.md or README.md"
            fail=1
        fi
    done
}

check_skills() {
    local dir="skills"
    [ -d "$dir" ] || return 0
    for f in "$dir"/*/SKILL.md; do
        [ -e "$f" ] || continue
        local name
        name="$(basename "$(dirname "$f")")"
        if ! grep -q -F "$name" "${docs[@]}"; then
            echo "DRIFT: skill '$name' (from $f) is not mentioned in CLAUDE.md or README.md"
            fail=1
        fi
    done
}

check_dir agents          md "agent"
check_skills
check_dir commands        md "command"
check_dir scripts/hooks   sh "hook script"
check_dir settings-templates json "settings template"
check_dir mcp-templates   json "MCP template"

if [ "$fail" -eq 1 ]; then
    echo ""
    echo "Documentation drift detected. Either:"
    echo "  - Add a mention of the missing item(s) to CLAUDE.md or README.md, OR"
    echo "  - If intentionally undocumented (e.g. internal CI helper), add a one-line note"
    echo "    to CLAUDE.md / README.md so this check passes."
    exit 1
fi

echo "No documentation drift detected."
