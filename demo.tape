# demo.tape — reproducible terminal recording for the README + LinkedIn post.
#
# Render:  brew install vhs  &&  vhs demo.tape   ->   docs/demo.gif
# Docs:    https://github.com/charmbracelet/vhs
#
# Run from the repo root. The hidden setup below puts scripts/ on PATH and
# moves into a throwaway sample project, so the visible demo reads like setting
# up a real project (not running inside this repo).

Output docs/demo.gif

Set Shell "bash"
Set FontSize 16
Set Width 1100
Set Height 760
Set Theme "Catppuccin Mocha"
Set Padding 20
Set TypingSpeed 45ms

# --- Hidden setup: portable, no machine-specific paths shown on screen ---
Hide
Type 'export PATH="$(pwd)/scripts:$PATH"'
Enter
Type "mkdir -p /tmp/acme-app && cd /tmp/acme-app"
Enter
Type "clear"
Enter
Show

# Settle the prompt before recording the first command.
Sleep 800ms

# --- 1. The menu of composable templates ---
Type "setup-project.sh --list"
Sleep 500ms
Enter
Sleep 3.5s

# --- 2. Compose two stacks into one project (dry-run — nothing is written) ---
Type "setup-project.sh --dry-run django react"
Sleep 500ms
Enter
Sleep 6s
