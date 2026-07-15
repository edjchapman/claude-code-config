---
name: later
description: Create a new "Later" backlog item (Learn / Research / Do / Read) from a configurable template.
argument-hint: "<title> [--category <name>] [--priority <level>]"
disable-model-invocation: true
---

Create a new "Later" item — a personal backlog entry for things to learn, research, do, or read.

> **Backlog location**: this command writes to `$LATER_DIR` (defaults to `~/notes/Later`). Set `LATER_DIR` in your shell if your backlog lives elsewhere.

## Arguments

`$ARGUMENTS`

- First positional argument is the **title** (required, can be quoted for multi-word)
- `--category <name>` — one of: Learn, Research, Do, Read (if omitted, ask the user)
- `--priority <level>` — Low, Medium, or High (default: Medium)
- Examples: `/later "Learn Rust async/await" --category Learn --priority High`, `/later "Read Designing Data-Intensive Applications"`, `/later "Set up home lab Kubernetes cluster" --category Do`

## Steps

1. **Parse arguments**: Extract the title, `--category`, and `--priority` from `$ARGUMENTS`.

   - The title is everything that is not a flag or flag value. It may be quoted.
   - `--priority` defaults to Medium if not provided.
   - If `--category` is missing, ask the user to choose one: Learn, Research, Do, Read.

2. **Resolve the backlog directory and template**:

   - Read `LATER_DIR` from the environment; if unset, default to `~/notes/Later`.
   - Look for a template file at `$LATER_DIR/_template.md`. If it exists, use it.
   - If no template file exists, fall back to this inline template:

     ```markdown
     # [Title]

     **Added:** YYYY-MM-DD
     **Priority:** Medium
     **Status:** New

     ## What

     ## Why

     ## Resources

     ## Notes
     ```

3. **Generate filename**: Convert the title to kebab-case for the filename.

   Note: the inline-fallback path skips step 2 ("Read the template") since the template is already inlined above.

   - Strip special characters (slashes, colons, quotes, etc.)
   - Example: "Learn Rust Async" → `learn-rust-async.md`

4. **Fill in metadata**: Copy the template and replace:

   - `# [Title]` → `# <the provided title>`
   - `**Added:** YYYY-MM-DD` → today's date
   - `**Priority:** Medium` → the chosen priority
   - `**Status:** New` → leave as New

5. **Gather content from the user**: Ask the user to provide content for each section. Ask all at once or in a natural flow:

   - **What** — brief description of the item
   - **Why** — why it's worth pursuing
   - **Resources** — any links, books, courses (optional — skip if user has none)
   - **Notes** — additional context (optional — skip if user has none)

6. **Write the file**: Save the completed file to `$LATER_DIR/<Category>/<filename>.md` (creating subdirectories as needed).

7. **Confirm**: Show the user the final file path and the rendered contents.

## Output

Display the created file path and its full contents so the user can verify everything looks correct.
