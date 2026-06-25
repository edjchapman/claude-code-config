#!/bin/bash
# Claude-on-web bootstrap — vendored into this repo by claude-code-config's
# `install-tooling.sh`. Wired via .claude/settings.json (SessionStart hook).
#
# Runs ONLY in remote/web sessions (CLAUDE_CODE_REMOTE=true); a no-op on local
# machines, which already have the toolchain + services. This file is yours now —
# edit freely. The stack detection is a best-effort default; tailor it (e.g. set
# DATABASE_URL, run migrations) for your project.
set -euo pipefail

# Local machines already have deps + services — skip.
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

# --- Install dependencies (stack-detected) ---------------------------------
# An explicit `make setup` target wins; otherwise detect the stack by lockfile.
if [ -f Makefile ] && grep -qE '^setup:' Makefile; then
  make setup
elif [ -f uv.lock ] || [ -f pyproject.toml ]; then
  if ! command -v uv > /dev/null 2>&1; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
  fi
  uv sync
elif [ -f package-lock.json ]; then
  npm ci
elif [ -f pnpm-lock.yaml ]; then
  corepack enable && pnpm install --frozen-lockfile
elif [ -f yarn.lock ]; then
  corepack enable && yarn install --frozen-lockfile
elif [ -f go.mod ]; then
  go mod download
fi

# --- Persist session env (customise per project) ---------------------------
# CLAUDE_ENV_FILE is sourced into each shell. Keep a freshly-installed uv on
# PATH, and add project env here — e.g. a test database URL when there's no
# Postgres in web sessions:
#   echo 'export DATABASE_URL="sqlite://:memory:"' >> "$CLAUDE_ENV_FILE"
if [ -n "${CLAUDE_ENV_FILE:-}" ]; then
  # shellcheck disable=SC2016  # literal export, expanded when CLAUDE_ENV_FILE is sourced
  echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$CLAUDE_ENV_FILE"
fi
