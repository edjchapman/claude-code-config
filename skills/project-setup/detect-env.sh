#!/usr/bin/env bash
# detect-env.sh — print the project facts the project-setup skill must not ask about.
#
# Why: the skill injects this via !`...`, and an injected command that exits
# non-zero aborts the whole skill invocation — Claude never sees the content.
# The primary use case is a brand-new empty directory, where nearly every probe
# here legitimately fails. So every probe is swallowed and the script always
# exits 0. Keep it that way.

# Print whichever of the named paths exist, space-separated. Never fails.
present() {
  local out="" p
  for p in "$@"; do
    [ -e "$p" ] && out="$out $p"
  done
  printf '%s' "${out# }"
}

echo "root: $(git rev-parse --show-toplevel 2>/dev/null || echo NONE)"
echo "remotes: $(git remote -v 2>/dev/null | head -1 || true)"
echo "manifests: $(present Cargo.toml package.json pyproject.toml go.mod Gemfile pom.xml build.gradle deno.json)"
echo "gate: $(present Makefile justfile Taskfile.yml)"
echo "hook manager: $(present .pre-commit-config.yaml lefthook.yml .husky)"
echo "hooksPath local: $(git config --local --get core.hooksPath 2>/dev/null || true)"
echo "hooksPath global: $(git config --global --get core.hooksPath 2>/dev/null || true)"
echo "ci: $(present .github/workflows .gitlab-ci.yml)"
echo "standard files: $(present README.md LICENSE CONTRIBUTING.md .gitignore)"
echo "claude config: $(present .claude)"

exit 0
