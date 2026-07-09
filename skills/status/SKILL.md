---
description: Capture a quick status update and append it to today's daily log.
argument-hint: "<message>"
disable-model-invocation: true
---

Capture a quick status update and append it to today's daily log.

## Arguments

`$ARGUMENTS`

- **Message**: Free-text status update (required)
  - Examples: `/status Finished auth flow for BIL-123`, `/status In code review for PR #456`

## Step 1: Parse Arguments

The full `$ARGUMENTS` text is the status message.

If no message is provided, ask the user:

> "What's your status update?"

## Step 2: Determine File Path

```bash
date +%Y-%m-%d
```

- Log file path: `./standups/YYYY-MM-DD-log.md`
- Create the `./standups/` directory if it doesn't exist

## Step 3: Create or Append to Daily Log

**If the log file does not exist**, create it with this header:

```markdown
# Daily Log - DD Mon YYYY
```

followed by a blank line and the `## Status Updates` section.

**Append** the timestamped entry under the `## Status Updates` section:

```markdown
- **HH:MM** - [message]
```

Use the current local time (24-hour format) for the timestamp.

**Important:** If the file already exists but has no `## Status Updates` section, add it before the first `## Session Summaries` section (or at the end of the file if no sections exist). Always append new entries at the end of the Status Updates section, before any other section.

## Step 4: Confirm

Output a brief confirmation (2-3 lines max):

```
Status logged to ./standups/YYYY-MM-DD-log.md
> HH:MM - [message]
```

Do NOT gather any additional data, run git commands, or produce lengthy output. This command is for quick capture only.
