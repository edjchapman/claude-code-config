#!/bin/bash
# Setup hook: detect project type and suggest configuration
# Used by: Setup (init) hook in settings.json

REPO_DIR="$(dirname "$(readlink -f ~/.claude/settings.json)")"

echo "=== Project Init ==="
echo ""

# Detect project type
DETECTED=()

if [ -f "requirements.txt" ] || [ -f "setup.py" ] || [ -f "setup.cfg" ] || [ -f "pyproject.toml" ]; then
  DETECTED+=("python")
fi

if [ -f "manage.py" ]; then
  DETECTED+=("django")
fi

if [ -f "package.json" ]; then
  if grep -q '"react"' package.json 2> /dev/null; then
    DETECTED+=("react")
  elif grep -q '"next"' package.json 2> /dev/null; then
    DETECTED+=("nextjs")
  else
    DETECTED+=("node")
  fi
fi

if [ -f "go.mod" ]; then
  DETECTED+=("go")
fi

if compgen -G "./*.tf" > /dev/null 2>&1; then
  DETECTED+=("terraform")
fi

if [ ${#DETECTED[@]} -gt 0 ]; then
  echo "Detected project types: ${DETECTED[*]}"
else
  echo "No specific project type detected."
fi

# Check if settings.local.json exists
if [ ! -f ".claude/settings.local.json" ]; then
  echo ""
  echo "No .claude/settings.local.json found."
  if [ ${#DETECTED[@]} -gt 0 ]; then
    echo "Suggestion: Run the following to configure permissions:"
    echo "  ${REPO_DIR}/scripts/setup-project.sh ${DETECTED[*]}"
  else
    echo "Run setup-project.sh with your desired templates to configure permissions."
    echo "  ${REPO_DIR}/scripts/setup-project.sh --list"
  fi
fi

echo ""
echo "Available commands: /commit, /review, /pr, /lint, /tdd, /standup"
echo "Available agents: @implement, @fix, @review-pr, @refactor, @ship"
echo ""
echo "=== End Project Init ==="
