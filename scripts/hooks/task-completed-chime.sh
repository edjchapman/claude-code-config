#!/usr/bin/env bash
# Emit a terminal bell when an autonomous task completes
# Used by: TaskCompleted hook in settings.json
#
# Surfaces completion of long autonomous runs without polling. The bell is
# non-intrusive (terminals can mute it) and doesn't depend on platform-
# specific notification daemons.

# Consume stdin payload (if any) but don't act on it — the bell is enough signal.
cat > /dev/null 2>&1 || true

# BEL (ASCII 7) — most terminals route this to the OS notification or audible bell.
printf '\a'

exit 0
