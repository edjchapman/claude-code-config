#!/usr/bin/env bash
# check-docs-drift.sh
#
# Fail CI if a git-tracked primitive isn't mentioned in CLAUDE.md or README.md.
# Catches the kind of drift where someone adds a new skill / agent /
# hook but forgets to document it. Both docs are searched together — either is
# sufficient mention; we only fail if neither references the file.
#
# Primitives are enumerated via `git ls-files` (not a directory scan) so the
# check matches what CI sees: untracked local-only extras — e.g. personal
# skills installed into a live-config clone and excluded via .git/info/exclude
# — never trip it.
#
# Run from repo root: scripts/check-docs-drift.sh

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

docs=(CLAUDE.md README.md)
fail=0

# Whole-name match: the name must not be embedded in a longer identifier.
# Substring matching let short names like 'pr' or 'later' pass via
# coincidental words ("approach", "translate"); require a non-name character
# (anything outside [A-Za-z0-9_-]) or line edge on both sides.
mentioned() {
    grep -q -E "(^|[^A-Za-z0-9_-])$1([^A-Za-z0-9_-]|$)" "${docs[@]}"
}

check_dir() {
    local dir="$1" ext="$2" label="$3"
    local f name
    while IFS= read -r f; do
        name="$(basename "$f" ."$ext")"
        if ! mentioned "$name"; then
            echo "DRIFT: $label '$name' (from $f) is not mentioned in CLAUDE.md or README.md"
            fail=1
        fi
    done < <(git ls-files -- "$dir" | grep -E "^$dir/[^/]+\.$ext\$" || true)
}

check_skills() {
    local f name
    while IFS= read -r f; do
        name="$(basename "$(dirname "$f")")"
        if ! mentioned "$name"; then
            echo "DRIFT: skill '$name' (from $f) is not mentioned in CLAUDE.md or README.md"
            fail=1
        fi
    done < <(git ls-files -- skills | grep -E '^skills/[^/]+/SKILL\.md$' || true)
}

check_dir agents          md "agent"
check_skills
check_dir scripts/hooks   sh "hook script"
check_dir settings-templates json "settings template"
check_dir mcp-templates   json "MCP template"

# Scheduling invariant (enforced here because the docs only state it in prose):
# skills fired by scheduled cloud routines must NOT set disable-model-invocation
# (the flag also blocks scheduled tasks, v2.1.196+), and the documented
# user-only skills MUST set it.
schedulable_skills=(standup eow-review)
user_only_skills=(status refinement later)

for s in "${schedulable_skills[@]}"; do
    f="skills/$s/SKILL.md"
    if [ -e "$f" ] && grep -q '^disable-model-invocation:[[:space:]]*true' "$f"; then
        echo "DRIFT: schedulable skill '$s' sets disable-model-invocation: true — this silently breaks the scheduled cloud routine that fires it"
        fail=1
    fi
done

for s in "${user_only_skills[@]}"; do
    f="skills/$s/SKILL.md"
    if [ -e "$f" ] && ! grep -q '^disable-model-invocation:[[:space:]]*true' "$f"; then
        echo "DRIFT: user-only skill '$s' is documented as disable-model-invocation: true but its frontmatter does not set it"
        fail=1
    fi
done

if [ "$fail" -eq 1 ]; then
    echo ""
    echo "Documentation drift detected. Either:"
    echo "  - Add a mention of the missing item(s) to CLAUDE.md or README.md, OR"
    echo "  - If intentionally undocumented (e.g. internal CI helper), add a one-line note"
    echo "    to CLAUDE.md / README.md so this check passes."
    exit 1
fi

echo "No documentation drift detected."
