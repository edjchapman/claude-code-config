#!/bin/bash
# Setup global Claude Code configuration on a new machine
#
# Usage:
#   ./setup-global.sh              # Auto-detects repo location
#   ./setup-global.sh /custom/path # Use custom path to repo
#
# This script creates symlinks in ~/.claude/ pointing to this repo's
# agents and commands directories.

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
  echo "  ├── commands/"
  echo "  ├── skills/"
  echo "  ├── rules/"
  echo "  └── scripts/setup-global.sh (this script)"
  exit 1
fi

if [ ! -d "$REPO_ROOT/commands" ]; then
  echo "Error: commands/ directory not found at: $REPO_ROOT"
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

# Remove existing symlinks/directories if they exist
for item in agents commands skills rules; do
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
ln -s "$REPO_ROOT/commands" ~/.claude/commands
ln -s "$REPO_ROOT/skills" ~/.claude/skills
ln -s "$REPO_ROOT/rules" ~/.claude/rules

# Handle settings.json symlink (plugin configuration)
if [ -L ~/.claude/settings.json ]; then
  echo "Removing existing symlink: ~/.claude/settings.json"
  rm ~/.claude/settings.json
elif [ -e ~/.claude/settings.json ]; then
  backup_file=~/.claude/settings.json.backup.$(date +%s)
  echo "Backing up existing file: ~/.claude/settings.json -> $backup_file"
  mv ~/.claude/settings.json "$backup_file"
fi

ln -s "$REPO_ROOT/settings.json" ~/.claude/settings.json

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

echo ""
echo "Global Claude Code config set up successfully!"
echo ""
echo "  ~/.claude/agents          -> $REPO_ROOT/agents"
echo "  ~/.claude/commands        -> $REPO_ROOT/commands"
echo "  ~/.claude/skills          -> $REPO_ROOT/skills"
echo "  ~/.claude/rules           -> $REPO_ROOT/rules"
echo "  ~/.claude/settings.json   -> $REPO_ROOT/settings.json"
echo "  ~/.claude/CLAUDE.md       -> $REPO_ROOT/home/CLAUDE.md"
echo ""
echo "Notes:"
echo "  - settings.json is now symlinked (universal plugin + hooks configuration)"
echo "  - settings.local.json remains local (machine-specific permissions)"
echo "  - Run setup-project.sh in project directories to set up per-project config"
echo ""
echo "Optional: enable personal plugins (Notion, Figma, frontend-design)"
echo "  These require external accounts and are intentionally not in the universal settings.json."
echo "  To enable them on this machine, merge enabledPlugins from:"
echo "    $REPO_ROOT/settings.personal.json.example"
echo "  into ~/.claude/settings.local.json (alongside your existing permissions block)."
echo ""
echo "Tip: Add these aliases to your shell profile:"
echo "  alias cr='~/Development/claude-code-config/scripts/cli/review-changes.sh'"
echo "  alias cpr='~/Development/claude-code-config/scripts/cli/review-pr.sh'"
echo "  alias cdr='~/Development/claude-code-config/scripts/cli/daily-report.sh'"
echo "  alias cee='~/Development/claude-code-config/scripts/cli/explain-error.sh'"
echo ""
echo "Verify with: ls -la ~/.claude/"
