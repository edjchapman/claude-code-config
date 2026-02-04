Create a new "Later" item from the template — a personal backlog entry for things to learn, research, do, or read.

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

2. **Read the template**: Read the file at `Later/_template.md` in this repository.

3. **Generate filename**: Convert the title to kebab-case for the filename.
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

6. **Write the file**: Save the completed file to `Later/<Category>/<filename>.md`.

7. **Confirm**: Show the user the final file path and the rendered contents.

## Output

Display the created file path and its full contents so the user can verify everything looks correct.