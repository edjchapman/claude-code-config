#!/bin/bash
# Setup project-level Claude Code configuration
#
# Usage:
#   ./setup-project.sh <type> [type2] ...   # Set up project with templates
#   ./setup-project.sh all                  # Set up with ALL templates
#   ./setup-project.sh --list               # Show available templates
#   ./setup-project.sh --check <types>      # Check for settings drift and symlinks
#   ./setup-project.sh --status             # Show current configuration state
#   ./setup-project.sh --dry-run <types>    # Preview changes without applying
#   ./setup-project.sh --help               # Show this help
#
# Examples:
#   ./setup-project.sh python               # Python project
#   ./setup-project.sh django react         # Full-stack Django + React
#   ./setup-project.sh all                  # All templates (full permissions)
#   ./setup-project.sh --check django       # Verify settings match templates
#   ./setup-project.sh --dry-run django     # Preview what would be created
#
# This script creates a .claude/ directory in your current project with:
#   - Symlinks to shared agents and commands
#   - Generated settings.local.json from merged templates

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
TEMPLATES_PATH="$REPO_ROOT/settings-templates"
MCP_TEMPLATES_PATH="$REPO_ROOT/mcp-templates"
DRY_RUN=false

# Extract the --tooling modifier (it can appear anywhere alongside the project
# types). Unlike a project type it is not a template — it triggers vendoring the
# hard-tooling layer (Makefile + validator scripts + CI workflows + git hooks)
# via scripts/install-tooling.sh after the Claude-layer setup. Strip it from the
# positional args here so the flag handlers below never see it.
INSTALL_TOOLING=false
_args=()
for _a in "$@"; do
  if [ "$_a" = "--tooling" ]; then
    INSTALL_TOOLING=true
  else
    _args+=("$_a")
  fi
done
set -- "${_args[@]}"

# `--tooling` with no project type → install only the tooling layer.
if [ "$INSTALL_TOOLING" = true ] && [ $# -eq 0 ]; then
  echo "Installing project tooling only (no Claude-layer templates)..."
  exec "$SCRIPT_DIR/install-tooling.sh" --hooks
fi

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
  echo "  $0 <type> [type2] ...      Set up project with specified templates"
  echo "  $0 all                     Set up with ALL templates"
  echo "  $0 --list, -l              Show available templates"
  echo "  $0 --check, -c <types>     Check settings drift and symlink integrity"
  echo "  $0 --status, -s            Show current configuration state"
  echo "  $0 --dry-run, -n <types>   Preview changes without applying"
  echo "  $0 <types> --tooling       Also vendor the hard-tooling layer (Makefile,"
  echo "                             scripts, CI, git hooks) — copied, not symlinked"
  echo "  $0 --help, -h              Show this help"
  echo ""
  echo "Available templates:"
  echo "  all       All templates below (full permissions)"
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
  echo "  $0 all                  # Everything (full permissions)"
  echo "  $0 go                   # Go project"
  echo "  $0 --check django       # Verify settings match templates"
  echo "  $0 --status             # Show what's currently configured"
  echo "  $0 --dry-run all        # Preview all templates"
  echo ""
  echo "This creates in your project:"
  echo "  .claude/"
  echo "  ├── agents              -> (symlink to repo agents)"
  echo "  ├── commands            -> (symlink to repo commands)"
  echo "  ├── skills              -> (symlink to repo skills)"
  echo "  ├── rules               -> (symlink to repo rules)"
  echo "  ├── settings.local.json (merged from base + your templates - permissions)"
  echo "  └── .mcp.json           (merged from mcp-templates - MCP server config)"
  echo ""
  echo "  Note: .claude/settings.json is NOT symlinked — your global ~/.claude/settings.json"
  echo "  already provides plugins + hooks. A committed .claude/settings.json + .claude/hooks/"
  echo "  (Claude-on-web bootstrap) come from the --tooling payload below."
  echo ""
  echo "With --tooling, additionally COPIES into the project root (idempotent, never clobbers):"
  echo "  Makefile, scripts/, .githooks/, .github/workflows/, .editorconfig, .markdownlint-cli2.jsonc,"
  echo "  .claude/hooks/session-start.sh, .claude/settings.json (Claude-on-web bootstrap)"
  echo "  (run scripts/install-tooling.sh directly for the tooling layer on its own)"
  echo "  --tooling applies to a setup run or --dry-run; it is ignored with --check/--list/--status."
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
  echo "  all       (all templates below)"
  for template in "$TEMPLATES_PATH"/*.json; do
    name=$(basename "$template" .json)
    echo "  $name"
  done
  echo ""
  echo "Usage: $0 <template> [template2] ..."
  echo "Note: 'base' is always included automatically"
  exit 0
fi

# Handle --status flag
if [ "$1" = "--status" ] || [ "$1" = "-s" ]; then
  echo "Claude Code Configuration Status"
  echo "================================="
  echo ""
  echo "Current directory: $(pwd)"
  echo ""

  if [ ! -d .claude ]; then
    echo "Status: Not configured (no .claude/ directory)"
    exit 0
  fi

  echo ".claude/ directory exists"
  echo ""

  # Check directory symlinks
  for item in agents commands skills rules; do
    if [ -L .claude/$item ]; then
      target=$(readlink .claude/$item)
      if [ -d .claude/$item ]; then
        echo "✓ $item -> $target"
      else
        echo "✗ $item -> $target (broken symlink)"
      fi
    elif [ -d .claude/$item ]; then
      echo "? $item (regular directory, not symlink)"
    else
      echo "✗ $item (missing)"
    fi
  done

  # Check settings file
  echo ""
  if [ -f .claude/settings.local.json ]; then
    echo "✓ settings.local.json exists"
    # Try to extract _generated_from
    if command -v python3 &> /dev/null; then
      generated_from=$(python3 -c "import json; d=json.load(open('.claude/settings.local.json')); print(' + '.join(d.get('_generated_from', ['unknown'])))" 2> /dev/null || echo "unknown")
      echo "  Generated from: $generated_from"
    fi
  else
    echo "✗ settings.local.json (missing)"
  fi

  echo ""
  if [ -f .mcp.json ]; then
    echo "✓ .mcp.json exists"
    if command -v python3 &> /dev/null; then
      server_count=$(python3 -c "import json; d=json.load(open('.mcp.json')); print(len(d.get('mcpServers', {})))" 2> /dev/null || echo "unknown")
      echo "  MCP servers configured: $server_count"
    fi
  else
    echo "- .mcp.json (not configured)"
  fi

  exit 0
fi

# Handle --dry-run flag
if [ "$1" = "--dry-run" ] || [ "$1" = "-n" ]; then
  shift
  DRY_RUN=true
  if [ $# -eq 0 ]; then
    echo "Usage: $0 --dry-run <project-type> [additional-types...]"
    echo "Preview what would be created without making changes."
    exit 1
  fi
fi

# Handle --check flag
if [ "$1" = "--check" ] || [ "$1" = "-c" ]; then
  shift
  if [ $# -eq 0 ]; then
    echo "Usage: $0 --check <project-type> [additional-types...]"
    echo "Check if project settings have drifted from canonical templates."
    exit 1
  fi

  HAS_ISSUES=false

  echo "Checking Claude Code configuration..."
  echo ""

  # Check symlinks
  for item in agents commands skills rules; do
    if [ -L .claude/$item ]; then
      target=$(readlink .claude/$item)
      if [ -d .claude/$item ]; then
        echo "✓ $item symlink OK -> $target"
      else
        echo "✗ $item symlink BROKEN -> $target"
        HAS_ISSUES=true
      fi
    elif [ -d .claude/$item ]; then
      echo "? $item is a regular directory (expected symlink)"
      HAS_ISSUES=true
    elif [ ! -e .claude/$item ]; then
      echo "✗ $item missing"
      HAS_ISSUES=true
    fi
  done

  echo ""

  # Check settings
  if [ ! -f .claude/settings.local.json ]; then
    echo "✗ No .claude/settings.local.json found"
    echo ""
    echo "Run '$0 $*' to create configuration."
    exit 1
  fi

  check_python

  EXPECTED=$(python3 "$SCRIPT_DIR/merge-settings.py" "$TEMPLATES_PATH" base "$@")
  CURRENT=$(cat .claude/settings.local.json)

  if [ "$EXPECTED" = "$CURRENT" ]; then
    echo "✓ Settings match templates (base $*)"
  else
    echo "✗ Settings have drifted from templates"
    HAS_ISSUES=true
  fi

  # Check .mcp.json if mcp-templates exist
  if [ -d "$MCP_TEMPLATES_PATH" ]; then
    echo ""
    if [ -f .mcp.json ]; then
      MCP_EXPECTED=$(python3 "$SCRIPT_DIR/merge-mcp.py" "$MCP_TEMPLATES_PATH" base "$@" 2> /dev/null)
      MCP_CURRENT=$(cat .mcp.json)
      if [ "$MCP_EXPECTED" = "$MCP_CURRENT" ]; then
        echo "✓ .mcp.json matches MCP templates (base $*)"
      else
        echo "✗ .mcp.json has drifted from MCP templates"
        HAS_ISSUES=true
      fi
    else
      echo "- .mcp.json not found (optional)"
    fi
  fi

  echo ""
  if [ "$HAS_ISSUES" = true ]; then
    echo "Issues found. To fix, run:"
    echo "  $0 $*"
    exit 1
  else
    echo "All checks passed!"
    exit 0
  fi
fi

# Show help if no arguments
if [ $# -eq 0 ]; then
  show_help
  exit 1
fi

# Collect all requested types
TYPES=("$@")

# Expand "all" to all available templates (excluding base, which is always included)
if [ "${TYPES[0]}" = "all" ]; then
  TYPES=()
  for template in "$TEMPLATES_PATH"/*.json; do
    name=$(basename "$template" .json)
    if [ "$name" != "base" ]; then
      TYPES+=("$name")
    fi
  done
  echo "Using all templates: ${TYPES[*]}"
  echo ""
fi

# Validate all types exist
for type in "${TYPES[@]}"; do
  if [ "$type" != "base" ] && [ ! -f "$TEMPLATES_PATH/$type.json" ]; then
    echo "Error: Unknown template '$type'"
    echo "Run '$0 --list' to see available templates"
    exit 1
  fi
done

# Validate repo structure
for item in agents commands skills rules; do
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

# Check Python early for dry-run preview
check_python

# Handle dry-run preview
if [ "$DRY_RUN" = true ]; then
  echo "Dry-run: Preview of changes (nothing will be modified)"
  echo "========================================================="
  echo ""
  echo "Directory: $(pwd)"
  echo ""
  echo "Would create:"
  echo "  .claude/"
  echo "  ├── agents              -> $REPO_ROOT/agents"
  echo "  ├── commands            -> $REPO_ROOT/commands"
  echo "  ├── skills              -> $REPO_ROOT/skills"
  echo "  ├── rules               -> $REPO_ROOT/rules"
  echo "  ├── settings.local.json"
  echo "  └── .mcp.json (project root)"
  echo ""
  echo "Generated settings.local.json content:"
  echo "---------------------------------------"
  python3 "$SCRIPT_DIR/merge-settings.py" "$TEMPLATES_PATH" base "${TYPES[@]}"
  echo ""
  if [ -d "$MCP_TEMPLATES_PATH" ]; then
    # Mirror the production filter: only include types that actually have MCP templates
    HAS_MCP=false
    MCP_TYPES=("base")
    for type in "${TYPES[@]}"; do
      if [ -f "$MCP_TEMPLATES_PATH/$type.json" ]; then
        HAS_MCP=true
        MCP_TYPES+=("$type")
      fi
    done
    if [ "$HAS_MCP" = true ]; then
      echo "Generated .mcp.json content:"
      echo "----------------------------"
      python3 "$SCRIPT_DIR/merge-mcp.py" "$MCP_TEMPLATES_PATH" "${MCP_TYPES[@]}"
      echo ""
    else
      echo "  (no MCP templates found for ${TYPES[*]}, no .mcp.json would be generated)"
      echo ""
    fi
  fi
  if [ "$INSTALL_TOOLING" = true ]; then
    echo "Project tooling (--tooling) — would copy into $(pwd):"
    "$SCRIPT_DIR/install-tooling.sh" --dry-run "${TYPES[@]}"
    echo ""
  fi
  echo "To apply these changes, run without --dry-run:"
  echo "  $0 ${TYPES[*]}"
  exit 0
fi

# Warn if Claude Code CLI is not installed (non-blocking)
if ! command -v claude &> /dev/null; then
  echo "Note: Claude Code CLI not found in PATH"
  echo "Install from: https://claude.ai/code"
  echo ""
fi

# Create .claude directory in current project
# Handle existing .claude (file, broken symlink, or symlink to non-directory)
if [ -L .claude ]; then
  # Remove any existing symlink (broken or otherwise)
  rm .claude
elif [ -e .claude ] && [ ! -d .claude ]; then
  echo "Error: .claude exists but is not a directory"
  echo "Please remove it first: rm .claude"
  exit 1
fi
# Use /bin/mkdir to avoid shell aliases that may not support -p
/bin/mkdir -p .claude || {
  echo "Error: Failed to create .claude directory"
  exit 1
}

# Remove existing symlinks if they exist
for item in agents commands skills rules; do
  if [ -L .claude/$item ]; then
    rm .claude/$item
  elif [ -e .claude/$item ]; then
    rm -rf .claude/$item
  fi
done

# Create symlinks to shared resources
ln -s "$REPO_ROOT/agents" .claude/agents
ln -s "$REPO_ROOT/commands" .claude/commands
ln -s "$REPO_ROOT/skills" .claude/skills
ln -s "$REPO_ROOT/rules" .claude/rules

# NOTE: .claude/settings.json is intentionally NOT symlinked. The global
# ~/.claude/settings.json (also -> this repo) already provides plugins + hooks,
# so a per-project symlink is redundant — and it would clobber a committed
# .claude/settings.json (the Claude-on-web bootstrap installed via --tooling).

echo "Generating settings.local.json (base + ${TYPES[*]})..."
python3 "$SCRIPT_DIR/merge-settings.py" "$TEMPLATES_PATH" base "${TYPES[@]}" > .claude/settings.local.json

# Generate .mcp.json if mcp-templates directory exists
if [ -d "$MCP_TEMPLATES_PATH" ]; then
  echo "Generating .mcp.json (base + ${TYPES[*]})..."
  # Only generate if at least one requested type has an MCP template
  HAS_MCP=false
  for type in "${TYPES[@]}"; do
    if [ -f "$MCP_TEMPLATES_PATH/$type.json" ]; then
      HAS_MCP=true
      break
    fi
  done
  if [ "$HAS_MCP" = true ]; then
    # Backup existing .mcp.json if it exists
    if [ -f .mcp.json ]; then
      backup_file=.mcp.json.backup.$(date +%s)
      echo "Backing up existing file: .mcp.json -> $backup_file"
      mv .mcp.json "$backup_file"
    fi
    # Build list of types that have MCP templates
    MCP_TYPES=("base")
    for type in "${TYPES[@]}"; do
      if [ -f "$MCP_TEMPLATES_PATH/$type.json" ]; then
        MCP_TYPES+=("$type")
      fi
    done
    python3 "$SCRIPT_DIR/merge-mcp.py" "$MCP_TEMPLATES_PATH" "${MCP_TYPES[@]}" > .mcp.json
  else
    echo "  (no MCP templates found for ${TYPES[*]}, skipping .mcp.json)"
  fi
fi

echo ""
echo "Project Claude Code config created!"
echo ""
echo "  .claude/agents              -> $REPO_ROOT/agents"
echo "  .claude/commands            -> $REPO_ROOT/commands"
echo "  .claude/skills              -> $REPO_ROOT/skills"
echo "  .claude/rules               -> $REPO_ROOT/rules"
echo "  .claude/settings.local.json (base + ${TYPES[*]})"
if [ -f .mcp.json ]; then
  echo "  .mcp.json                   (MCP server config)"
fi
echo ""
echo "Verify: ls -la .claude/"

# Vendor the hard-tooling layer (Makefile + scripts + CI + git hooks) if requested.
if [ "$INSTALL_TOOLING" = true ]; then
  echo ""
  echo "Installing project tooling (--tooling)..."
  "$SCRIPT_DIR/install-tooling.sh" --hooks "${TYPES[@]}"
fi
