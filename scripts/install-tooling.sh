#!/usr/bin/env bash
# install-tooling.sh — vendor the project hard-tooling layer into a target repo.
#
# Copies the tooling/ payload (Makefile, validator scripts, git hooks, CI
# workflows, .editorconfig, .markdownlint-cli2.jsonc) into a project. Unlike the
# Claude layer (symlinked so updates propagate), the hard tooling is COPIED:
# GitHub Actions only runs workflows physically present in the project's own
# committed tree, and the Makefile/scripts/hooks become part of that repo's
# source. There is no auto-propagation — re-run to pick up new payload files.
#
# Idempotent: copy-if-absent, never clobber. A second run reports all-skipped
# and leaves the working tree unchanged.
#
# Usage:
#   install-tooling.sh [--dry-run] [--hooks] [--target DIR] [STACK ...]
#
#   STACK ...        optional stack hints (python, node, go, ...) — used ONLY to
#                    print a suggested stack-check snippet; nothing is auto-wired
#   --target DIR     project root to install into (default: current directory)
#   --dry-run, -n    print what would happen; change nothing
#   --hooks          also run `git config core.hooksPath .githooks` in the target
#   -h, --help       show this help
#
# Called by `setup-project.sh --tooling`, or run standalone.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
PAYLOAD="$REPO_ROOT/tooling"

DRY_RUN=false
WIRE_HOOKS=false
TARGET=""
STACKS=()

while [ $# -gt 0 ]; do
  case "$1" in
    --dry-run | -n) DRY_RUN=true ;;
    --hooks) WIRE_HOOKS=true ;;
    --target)
      shift
      TARGET="${1:-}"
      ;;
    -h | --help)
      grep '^#' "$0" | grep -v '^#!' | sed 's/^# \{0,1\}//'
      exit 0
      ;;
    --*)
      echo "install-tooling: unknown flag: $1" >&2
      exit 2
      ;;
    *) STACKS+=("$1") ;;
  esac
  shift
done

[ -z "$TARGET" ] && TARGET="."
if [ ! -d "$TARGET" ]; then
  echo "install-tooling: target directory does not exist: $TARGET" >&2
  exit 1
fi
TARGET="$(cd "$TARGET" && pwd)"

if [ ! -d "$PAYLOAD" ]; then
  echo "install-tooling: payload not found at $PAYLOAD" >&2
  exit 1
fi

added=0
skipped=0

# copy_file SRC DST_REL — copy payload SRC to TARGET/DST_REL if absent.
copy_file() {
  local src="$1"
  local dst_rel="$2"
  local dst="$TARGET/$2"
  if [ -e "$dst" ]; then
    echo "  skip   $dst_rel (exists)"
    skipped=$((skipped + 1))
    return
  fi
  if [ "$DRY_RUN" = true ]; then
    echo "  add    $dst_rel"
    added=$((added + 1))
    return
  fi
  mkdir -p "$(dirname "$dst")"
  cp "$src" "$dst"
  # Preserve executability for scripts and git hooks (pre-commit enforces this).
  case "$dst_rel" in
    scripts/*.sh | scripts/*.py | .githooks/*) chmod +x "$dst" ;;
  esac
  echo "  add    $dst_rel"
  added=$((added + 1))
}

echo "Installing project tooling into: $TARGET"
[ "$DRY_RUN" = true ] && echo "(dry run — no changes will be made)"
echo ""

# Makefile + dotfile configs (payload stores dotfiles un-dotted; dot them here).
copy_file "$PAYLOAD/Makefile" "Makefile"
copy_file "$PAYLOAD/editorconfig" ".editorconfig"
copy_file "$PAYLOAD/markdownlint-cli2.jsonc" ".markdownlint-cli2.jsonc"

# Validator scripts.
for f in "$PAYLOAD"/scripts/*; do
  [ -e "$f" ] || continue
  copy_file "$f" "scripts/$(basename "$f")"
done

# Git hooks (target activates them via core.hooksPath .githooks).
for f in "$PAYLOAD"/githooks/*; do
  [ -e "$f" ] || continue
  copy_file "$f" ".githooks/$(basename "$f")"
done

# CI workflows.
for f in "$PAYLOAD"/github/workflows/*; do
  [ -e "$f" ] || continue
  copy_file "$f" ".github/workflows/$(basename "$f")"
done

echo ""
echo "Summary: $added added, $skipped skipped."

# Optionally wire git hooks.
if [ "$WIRE_HOOKS" = true ]; then
  if [ "$DRY_RUN" = true ]; then
    echo "Would set: git config core.hooksPath .githooks (in $TARGET)"
  elif git -C "$TARGET" rev-parse --git-dir > /dev/null 2>&1; then
    git -C "$TARGET" config core.hooksPath .githooks
    echo "Wired: core.hooksPath = .githooks"
  else
    echo "Note: $TARGET is not a git repo — skipped core.hooksPath wiring."
  fi
fi

# Stack hint (suggestion only; nothing is auto-wired into the Makefile).
if [ "${#STACKS[@]}" -gt 0 ]; then
  printed_header=false
  for s in "${STACKS[@]}"; do
    [ "$s" = "base" ] && continue
    if [ "$printed_header" = false ]; then
      echo ""
      echo "Stack hint — wire the 'stack-check' target in your Makefile:"
      printed_header=true
    fi
    case "$s" in
      python | django | fastapi)
        echo "  $s: stack-check: ; @ruff check . && pytest -q" ;;
      node | react | nextjs)
        echo "  $s: stack-check: ; @npm run lint && npm test" ;;
      go)
        echo "  $s: stack-check: ; @go vet ./... && go test ./..." ;;
      rust)
        echo "  $s: stack-check: ; @cargo clippy && cargo test" ;;
      *)
        echo "  $s: (no snippet — add your lint/test to the stack-check target)" ;;
    esac
  done
fi

echo ""
echo "Next steps:"
echo "  - Review the vendored Makefile and wire 'stack-check' to your lint/test."
echo "  - Activate git hooks:  git config core.hooksPath .githooks"
echo "  - Run the gate:        make check"
