#!/usr/bin/env bash
# Forward session events to iTerm2's Claude Code status integration.
#
# Why: iTerm2 ships a `cc-status` helper that renders live session state in the
# terminal's status bar, and its installer registers that helper directly in
# ~/.claude/settings.json. Because `hooks` is a managed key (ADR-0002), every
# sync then reported drift and setup-global.sh would have wiped all ten
# registrations. Wiring it through the repo's own hook definitions (ADR-0001)
# makes the integration survive a sync instead of fighting it.
#
# The helper is machine-specific — it lives inside iTerm.app, and this repo is
# installed as a plugin on machines that have no iTerm2 — so its absence is the
# normal case, not an error. This script exits 0 either way and never blocks a
# tool call, which matters because it is wired on PreToolUse.

set -u

HELPER="${HOME}/.config/iterm2/cc-status"
[ -x "$HELPER" ] || exit 0

# Pass the payload through untouched, but never let a status helper's exit code
# reach the harness: a non-zero exit on PreToolUse would block the tool call.
"$HELPER" || true
exit 0
