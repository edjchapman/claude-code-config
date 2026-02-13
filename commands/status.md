Capture a quick status update and append it to today's daily log.

## Arguments

`$ARGUMENTS`

- **Message**: Free-text status update (required)
  - Examples: `/status Finished auth flow for BIL-123`, `/status In code review for PR #456`
- **Notion sync**: `--notion` - Also append this entry to today's Notion standup page

## Step 1: Parse Arguments

Parse `$ARGUMENTS` for:
1. **`--notion` flag**: If present, remove it from the message and set a flag to sync to Notion
2. **Message**: Everything remaining after flag removal is the status message

If no message is provided (empty after flag removal), ask the user:
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

If `--notion` flag was provided, tag the entry:

```markdown
- **HH:MM** - [notion] [message]
```

Use the current local time (24-hour format) for the timestamp.

**Important:** If the file already exists but has no `## Status Updates` section, add it before the first `## Session Summaries` section (or at the end of the file if no sections exist). Always append new entries at the end of the Status Updates section, before any other section.

## Step 4: Notion Sync (only if `--notion` flag)

**If `--notion` flag was provided AND Notion MCP is available (`mcp__plugin_Notion_notion__*` tools):**

1. Use `mcp__plugin_Notion_notion__notion-search` to find today's standup page
   - Search for today's date in page titles (e.g., "11 Feb 2026" or "2026-02-11")
   - Look for pages with "standup" or "daily" in the title
2. If a page is found, use `mcp__plugin_Notion_notion__notion-update-page` to append the status entry
3. If no page is found, note this in the confirmation message

**If Notion MCP is NOT available:**
Skip Notion sync and note in the confirmation that Notion sync was requested but unavailable.

## Step 5: Confirm

Output a brief confirmation (2-3 lines max):

```
Status logged to ./standups/YYYY-MM-DD-log.md
> HH:MM - [message]
```

If Notion was synced: add `(also synced to Notion)`
If Notion sync failed: add `(Notion sync: page not found)` or similar brief note

Do NOT gather any additional data, run git commands, or produce lengthy output. This command is for quick capture only.
