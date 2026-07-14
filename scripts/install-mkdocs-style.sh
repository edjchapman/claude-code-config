#!/usr/bin/env bash
# install-mkdocs-style.sh — vendor the shared MkDocs Material style layer
# ("Ink & Indigo on warm paper") into a target project.
#
# Copies the tooling/mkdocs/ payload into a project and wires it up via MkDocs
# native config inheritance:
#   mkdocs.style.yml  -> <target>/mkdocs.style.yml          (theme + extensions)
#   custom.css        -> <target>/<css-dest>                (palette stylesheet)
# and inserts `INHERIT: mkdocs.style.yml` at the top of mkdocs.yml if missing.
#
# UNLIKE install-tooling.sh (copy-if-absent), the two style-owned files are
# ALWAYS OVERWRITTEN — re-running this script IS the update mechanism. Nothing
# else in the target is ever modified; conflicting keys in the project's
# mkdocs.yml are reported as warnings only (MkDocs merges mappings per-key but
# REPLACES lists wholesale, so a leftover theme.features/palette,
# markdown_extensions, or extra_css list silently discards the shared layer).
#
# Usage:
#   install-mkdocs-style.sh [--target DIR] [--css-dest REL] [--dry-run]
#
#   --target DIR     project root to install into (default: current directory)
#   --css-dest REL   destination for custom.css, relative to target
#                    (default: docs/stylesheets/custom.css; use e.g.
#                    mkdocs-theme/stylesheets/custom.css for projects with a
#                    generated docs tree)
#   --dry-run, -n    print what would happen; change nothing
#   -h, --help       show this help
#
# The /mkdocs-style Claude skill wraps this script and also removes the
# now-redundant keys from the project's mkdocs.yml.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
PAYLOAD="$REPO_ROOT/tooling/mkdocs"

DRY_RUN=false
TARGET=""
CSS_DEST="docs/stylesheets/custom.css"

while [ $# -gt 0 ]; do
  case "$1" in
    --dry-run | -n) DRY_RUN=true ;;
    --target)
      shift
      TARGET="${1:-}"
      ;;
    --css-dest)
      shift
      CSS_DEST="${1:-}"
      ;;
    -h | --help)
      grep '^#' "$0" | grep -v '^#!' | sed 's/^# \{0,1\}//'
      exit 0
      ;;
    --*)
      echo "install-mkdocs-style: unknown flag: $1" >&2
      exit 2
      ;;
    *)
      echo "install-mkdocs-style: unexpected argument: $1" >&2
      exit 2
      ;;
  esac
  shift
done

[ -z "$TARGET" ] && TARGET="."
if [ ! -d "$TARGET" ]; then
  echo "install-mkdocs-style: target directory does not exist: $TARGET" >&2
  exit 1
fi
TARGET="$(cd "$TARGET" && pwd)"

if [ ! -d "$PAYLOAD" ]; then
  echo "install-mkdocs-style: payload not found at $PAYLOAD" >&2
  exit 1
fi
if [ ! -f "$TARGET/mkdocs.yml" ]; then
  echo "install-mkdocs-style: no mkdocs.yml in $TARGET — not an MkDocs project?" >&2
  exit 1
fi

added=0
updated=0
unchanged=0

# sync_file SRC DST_REL — copy payload SRC to TARGET/DST_REL, overwriting.
# Style-owned files: overwrite is the update mechanism. cmp first so an
# idempotent re-run reports unchanged and leaves the working tree untouched.
sync_file() {
  local src="$1"
  local dst_rel="$2"
  local dst="$TARGET/$dst_rel"
  if [ -e "$dst" ] && cmp -s "$src" "$dst"; then
    echo "  unchanged  $dst_rel"
    unchanged=$((unchanged + 1))
    return
  fi
  local verb="add"
  [ -e "$dst" ] && verb="update"
  if [ "$DRY_RUN" = true ]; then
    echo "  $verb    $dst_rel"
  else
    mkdir -p "$(dirname "$dst")"
    cp "$src" "$dst"
    echo "  $verb    $dst_rel"
  fi
  if [ "$verb" = "add" ]; then added=$((added + 1)); else updated=$((updated + 1)); fi
}

echo "Installing mkdocs style layer into: $TARGET"
[ "$DRY_RUN" = true ] && echo "(dry run — no changes will be made)"
echo ""

sync_file "$PAYLOAD/mkdocs.style.yml" "mkdocs.style.yml"
sync_file "$PAYLOAD/custom.css" "$CSS_DEST"

# Wire INHERIT as the first non-comment line of mkdocs.yml if not present.
if grep -q '^INHERIT:' "$TARGET/mkdocs.yml"; then
  echo "  unchanged  mkdocs.yml (INHERIT already present)"
else
  if [ "$DRY_RUN" = true ]; then
    echo "  update  mkdocs.yml (insert INHERIT: mkdocs.style.yml)"
  else
    awk 'BEGIN { done = 0 }
         !done && !/^#/ { print "INHERIT: mkdocs.style.yml"; done = 1 }
         { print }' "$TARGET/mkdocs.yml" > "$TARGET/mkdocs.yml.tmp"
    mv "$TARGET/mkdocs.yml.tmp" "$TARGET/mkdocs.yml"
    echo "  update  mkdocs.yml (inserted INHERIT: mkdocs.style.yml)"
  fi
  updated=$((updated + 1))
fi

echo ""
echo "Summary: $added added, $updated updated, $unchanged unchanged."

# Conflict scan (report-only): keys in the child config that shadow the shared
# layer. Lists REPLACE wholesale on merge, so these silently discard the layer.
warnings=()
grep -q '^markdown_extensions:' "$TARGET/mkdocs.yml" \
  && warnings+=("markdown_extensions: (child list replaces the shared set)")
grep -Eq '^\s+features:' "$TARGET/mkdocs.yml" \
  && warnings+=("theme.features: (child list replaces the shared set)")
grep -Eq '^\s+palette:' "$TARGET/mkdocs.yml" \
  && warnings+=("theme.palette: (child list replaces the shared palette)")
grep -Eq '^\s+font:' "$TARGET/mkdocs.yml" \
  && warnings+=("theme.font: (already provided by the shared layer)")
grep -Eq '^\s+name: material' "$TARGET/mkdocs.yml" \
  && warnings+=("theme.name: (already provided by the shared layer)")
if grep -q '^extra_css:' "$TARGET/mkdocs.yml" \
  && ! grep -A 5 '^extra_css:' "$TARGET/mkdocs.yml" | grep -q 'stylesheets/custom.css'; then
  warnings+=("extra_css: (child list omits stylesheets/custom.css — palette will not load)")
fi
grep -Eq '^\s+generator:' "$TARGET/mkdocs.yml" \
  && warnings+=("extra.generator: (already provided by the shared layer)")

if [ "${#warnings[@]}" -gt 0 ]; then
  echo ""
  echo "WARNING — mkdocs.yml defines keys that shadow the shared layer:"
  for w in "${warnings[@]}"; do
    echo "  - $w"
  done
  echo "Remove them (or run the /mkdocs-style skill, which does this for you)."
fi

echo ""
echo "Next steps:"
echo "  - Remove any warned keys above from mkdocs.yml (branding keys like"
echo "    theme.favicon / theme.logo / theme.icon.logo are fine to keep)."
echo "  - Ensure $CSS_DEST is reachable from docs_dir as stylesheets/custom.css."
echo "  - Verify: mkdocs build --strict (or the project's make check)."
