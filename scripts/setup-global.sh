#!/usr/bin/env bash
# Setup global Claude Code configuration on a new machine
#
# Usage:
#   ./setup-global.sh              # Auto-detects repo location
#   ./setup-global.sh /custom/path # Use custom path to repo
#
# This script creates symlinks in ~/.claude/ pointing to this repo's
# agents, skills, and rules directories, and mirrors settings.json into
# ~/.claude/settings.json (a real file, not a symlink — ADR-0002).

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="${1:-$(dirname "$SCRIPT_DIR")}"

# Validate repo structure
if [ ! -d "$REPO_ROOT/agents" ]; then
  echo "Error: agents/ directory not found at: $REPO_ROOT"
  echo ""
  echo "Expected directory structure:"
  echo "  $REPO_ROOT/"
  echo "  ├── agents/"
  echo "  ├── skills/"
  echo "  ├── rules/"
  echo "  └── scripts/setup-global.sh (this script)"
  exit 1
fi

if [ ! -d "$REPO_ROOT/skills" ]; then
  echo "Error: skills/ directory not found at: $REPO_ROOT"
  exit 1
fi

if [ ! -d "$REPO_ROOT/rules" ]; then
  echo "Error: rules/ directory not found at: $REPO_ROOT"
  exit 1
fi

if [ ! -f "$REPO_ROOT/home/CLAUDE.md" ]; then
  echo "Error: home/CLAUDE.md not found at: $REPO_ROOT"
  exit 1
fi

# Warn if Claude Code CLI is not installed (non-blocking)
if ! command -v claude &> /dev/null; then
  echo "Note: Claude Code CLI not found in PATH"
  echo "Install from: https://claude.ai/code"
  echo ""
fi

echo "Setting up global Claude Code config..."
echo "Repository: $REPO_ROOT"
echo ""

# Create ~/.claude if it doesn't exist
mkdir -p ~/.claude

# Legacy cleanup: the repo's former commands/ layout was merged into skills/,
# so remove a stale ~/.claude/commands SYMLINK from older installs. Symlinks
# only — a real ~/.claude/commands directory (personal slash commands,
# unrelated to this repo) must never be deleted.
if [ -L ~/.claude/commands ]; then
  echo "Removing stale legacy symlink: ~/.claude/commands"
  rm ~/.claude/commands
fi

# Remove existing symlinks/directories if they exist (each is recreated below)
for item in agents skills rules; do
  if [ -L ~/.claude/$item ]; then
    echo "Removing existing symlink: ~/.claude/$item"
    rm ~/.claude/$item
  elif [ -e ~/.claude/$item ]; then
    echo "Removing existing directory: ~/.claude/$item"
    rm -rf ~/.claude/$item
  fi
done

# Create symlinks
ln -s "$REPO_ROOT/agents" ~/.claude/agents
ln -s "$REPO_ROOT/skills" ~/.claude/skills
ln -s "$REPO_ROOT/rules" ~/.claude/rules

# Handle CLAUDE.md symlink (global cross-project behavioural rules)
if [ -L ~/.claude/CLAUDE.md ]; then
  echo "Removing existing symlink: ~/.claude/CLAUDE.md"
  rm ~/.claude/CLAUDE.md
elif [ -e ~/.claude/CLAUDE.md ]; then
  backup_file=~/.claude/CLAUDE.md.backup.$(date +%s)
  echo "Backing up existing file: ~/.claude/CLAUDE.md -> $backup_file"
  mv ~/.claude/CLAUDE.md "$backup_file"
fi

ln -s "$REPO_ROOT/home/CLAUDE.md" ~/.claude/CLAUDE.md

# Mirror settings.json into ~/.claude/settings.json (ADR-0002). A real file,
# deliberately NOT a symlink: Claude Code writes user-scope settings (/model,
# /config toggles, permission approvals) to this path at runtime, and a
# symlink would land every one of those writes as a pending diff in this
# repo. The sync mirrors managed keys and preserves personal ones.
# Deliberately the LAST step: it refuses to touch an unparseable target and
# exits 1, and under `set -e` that must abort with every symlink (including
# CLAUDE.md) already in place, not leave a half-installed tree.
python3 "$SCRIPT_DIR/sync-global-settings.py" --source-root "$REPO_ROOT"

echo ""
echo "Global Claude Code config set up successfully!"
echo ""
echo "  ~/.claude/agents          -> $REPO_ROOT/agents"
echo "  ~/.claude/skills          -> $REPO_ROOT/skills"
echo "  ~/.claude/rules           -> $REPO_ROOT/rules"
echo "  ~/.claude/settings.json   <- mirrored from $REPO_ROOT/settings.json"
echo "  ~/.claude/CLAUDE.md       -> $REPO_ROOT/home/CLAUDE.md"
echo ""
echo "Notes:"
echo "  - settings.json is a mirrored real file, not a symlink (ADR-0002):"
echo "    managed keys track the repo; personal keys (model, permissions,"
echo "    extra enabledPlugins entries) stay yours and survive every sync."
echo "  - After editing settings in the repo, re-run this script (or"
echo "    scripts/sync-global-settings.py) to apply; a SessionStart hook warns"
echo "    when the mirror has drifted."
echo "  - Run setup-project.sh in project directories to set up per-project config"
echo ""
echo "Optional: enable personal plugins (e.g. Figma) that need external accounts"
echo "  by adding their entries to enabledPlugins in ~/.claude/settings.json —"
echo "  the sync preserves entries the repo does not declare."
echo ""
echo "Tip: Add these aliases to your shell profile:"
echo "  alias cr='$REPO_ROOT/scripts/cli/review-changes.sh'"
echo "  alias cpr='$REPO_ROOT/scripts/cli/review-pr.sh'"
echo "  alias cdr='$REPO_ROOT/scripts/cli/daily-report.sh'"
echo "  alias cee='$REPO_ROOT/scripts/cli/explain-error.sh'"
echo ""
echo "Verify with: ls -la ~/.claude/"
