#!/bin/bash
# Setup project-level Claude Code configuration
#
# Usage:
#   ./setup-project.sh <type> [type2] ...   # Set up project with templates
#   ./setup-project.sh --list               # Show available templates
#   ./setup-project.sh --check <types>      # Check for settings drift
#   ./setup-project.sh --help               # Show this help
#
# Examples:
#   ./setup-project.sh python               # Python project
#   ./setup-project.sh django react         # Full-stack Django + React
#   ./setup-project.sh --check django       # Verify settings match templates
#
# This script creates a .claude/ directory in your current project with:
#   - Symlinks to shared agents and commands
#   - Generated settings.local.json from merged templates

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
TEMPLATES_PATH="$REPO_ROOT/settings-templates"

# Check Python 3.8+ is available
check_python() {
    if ! command -v python3 &> /dev/null; then
        echo "Error: python3 not found in PATH"
        echo "Please install Python 3.8 or later"
        exit 1
    fi

    PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
    PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)

    if [ "$PYTHON_MAJOR" -lt 3 ] || { [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]; }; then
        echo "Error: Python 3.8+ required, but found Python $PYTHON_VERSION"
        exit 1
    fi
}

# Show help
show_help() {
    echo "Setup project-level Claude Code configuration"
    echo ""
    echo "Usage:"
    echo "  $0 <type> [type2] ...   Set up project with specified templates"
    echo "  $0 --list, -l           Show available templates"
    echo "  $0 --check, -c <types>  Check if settings have drifted from templates"
    echo "  $0 --help, -h           Show this help"
    echo ""
    echo "Available templates:"
    echo "  base      Git, GitHub CLI, basic file operations (always included)"
    echo "  python    Python: pytest, mypy, ruff, pip, uv, poetry"
    echo "  django    Django: pytest, docker compose, uv, make"
    echo "  react     React/TypeScript: npm, vitest, playwright"
    echo "  node      Node.js: npm, yarn, pnpm, vitest, eslint"
    echo "  go        Go: go build/test/run, golangci-lint"
    echo "  terraform Terraform: fmt, validate, plan, init"
    echo ""
    echo "Examples:"
    echo "  $0 python               # Python project"
    echo "  $0 django               # Django project"
    echo "  $0 react                # React frontend"
    echo "  $0 django react         # Full-stack Django + React"
    echo "  $0 go                   # Go project"
    echo "  $0 --check django       # Verify settings match templates"
    echo ""
    echo "This creates in your project:"
    echo "  .claude/"
    echo "  ├── agents   -> (symlink to repo agents)"
    echo "  ├── commands -> (symlink to repo commands)"
    echo "  └── settings.local.json (merged from base + your templates)"
}

# Handle --help flag
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    show_help
    exit 0
fi

# Handle --list flag
if [ "$1" = "--list" ] || [ "$1" = "-l" ]; then
    echo "Available templates:"
    echo ""
    for template in "$TEMPLATES_PATH"/*.json; do
        name=$(basename "$template" .json)
        echo "  $name"
    done
    echo ""
    echo "Usage: $0 <template> [template2] ..."
    echo "Note: 'base' is always included automatically"
    exit 0
fi

# Handle --check flag
if [ "$1" = "--check" ] || [ "$1" = "-c" ]; then
    shift
    if [ $# -eq 0 ]; then
        echo "Usage: $0 --check <project-type> [additional-types...]"
        echo "Check if project settings have drifted from canonical templates."
        exit 1
    fi

    if [ ! -f .claude/settings.local.json ]; then
        echo "Error: No .claude/settings.local.json found in current directory"
        echo "Run '$0 $*' to create it first."
        exit 1
    fi

    check_python

    EXPECTED=$(python3 "$SCRIPT_DIR/merge-settings.py" "$TEMPLATES_PATH" base "$@")
    CURRENT=$(cat .claude/settings.local.json)

    if [ "$EXPECTED" = "$CURRENT" ]; then
        echo "✓ Settings are in sync with templates (base $*)"
        exit 0
    else
        echo "⚠ Settings have drifted from templates"
        echo ""
        echo "To regenerate from templates, run:"
        echo "  $0 $*"
        exit 1
    fi
fi

# Show help if no arguments
if [ $# -eq 0 ]; then
    show_help
    exit 1
fi

# Collect all requested types
TYPES=("$@")

# Validate all types exist
for type in "${TYPES[@]}"; do
    if [ "$type" != "base" ] && [ ! -f "$TEMPLATES_PATH/$type.json" ]; then
        echo "Error: Unknown template '$type'"
        echo "Run '$0 --list' to see available templates"
        exit 1
    fi
done

# Validate repo structure
for item in agents commands; do
    if [ ! -d "$REPO_ROOT/$item" ]; then
        echo "Error: $REPO_ROOT/$item does not exist"
        echo "The repository structure appears incomplete."
        exit 1
    fi
    if [ -L "$REPO_ROOT/$item" ]; then
        echo "Error: $REPO_ROOT/$item is a symlink, not a real directory"
        echo "Run this script from the actual repository, not a symlinked location."
        exit 1
    fi
done

# Prevent running from within the repo itself (would create circular symlinks)
CURRENT_DIR="$(cd "$(pwd)" && pwd)"
if [ "$CURRENT_DIR" = "$REPO_ROOT" ] || [ "$CURRENT_DIR/.claude" = "$REPO_ROOT" ]; then
    echo "Error: Cannot run setup-project.sh from within the config repository"
    echo "This would create circular symlinks."
    echo ""
    echo "Run this from your actual project directory:"
    echo "  cd ~/your-project"
    echo "  $0 ${TYPES[*]}"
    exit 1
fi

# Create .claude directory in current project
mkdir -p .claude

# Remove existing symlinks if they exist
for item in agents commands; do
    if [ -L .claude/$item ]; then
        rm .claude/$item
    elif [ -e .claude/$item ]; then
        rm -rf .claude/$item
    fi
done

# Create symlinks to shared resources
ln -s "$REPO_ROOT/agents" .claude/agents
ln -s "$REPO_ROOT/commands" .claude/commands

# Check Python and generate settings
check_python

echo "Generating settings.local.json (base + ${TYPES[*]})..."
python3 "$SCRIPT_DIR/merge-settings.py" "$TEMPLATES_PATH" base "${TYPES[@]}" > .claude/settings.local.json

echo ""
echo "Project Claude Code config created!"
echo ""
echo "  .claude/agents            -> $REPO_ROOT/agents"
echo "  .claude/commands          -> $REPO_ROOT/commands"
echo "  .claude/settings.local.json (base + ${TYPES[*]})"
echo ""
echo "Verify: ls -la .claude/"