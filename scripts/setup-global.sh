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
    echo "  └── scripts/setup-global.sh (this script)"
    exit 1
fi

if [ ! -d "$REPO_ROOT/commands" ]; then
    echo "Error: commands/ directory not found at: $REPO_ROOT"
    exit 1
fi

echo "Setting up global Claude Code config..."
echo "Repository: $REPO_ROOT"
echo ""

# Create ~/.claude if it doesn't exist
mkdir -p ~/.claude

# Remove existing symlinks/directories if they exist
for item in agents commands; do
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

echo ""
echo "Global Claude Code config set up successfully!"
echo ""
echo "  ~/.claude/agents   -> $REPO_ROOT/agents"
echo "  ~/.claude/commands -> $REPO_ROOT/commands"
echo ""
echo "Notes:"
echo "  - settings.local.json remains local (machine-specific permissions)"
echo "  - Run setup-project.sh in project directories to set up per-project config"
echo ""
echo "Verify with: ls -la ~/.claude/"