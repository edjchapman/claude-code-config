# demo.tape — reproducible terminal recording for the README + LinkedIn post.
#
# Render:  brew install vhs  &&  vhs demo.tape   ->   docs/demo.gif
# Docs:    https://github.com/charmbracelet/vhs
#
# Run from the repo root so the relative `scripts/...` paths resolve.

Output docs/demo.gif

Set Shell "bash"
Set FontSize 16
Set Width 1100
Set Height 760
Set Theme "Catppuccin Mocha"
Set Padding 20
Set TypingSpeed 45ms

# Settle the prompt before recording the first command.
Sleep 800ms

# --- 1. The menu of composable templates ---
Type "scripts/setup-project.sh --list"
Sleep 500ms
Enter
Sleep 3.5s

# --- 2. Compose two stacks into one project (dry-run — nothing is written) ---
Type "scripts/setup-project.sh --dry-run django react"
Sleep 500ms
Enter
Sleep 6s
