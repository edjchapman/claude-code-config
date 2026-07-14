---
description: Install or update the shared MkDocs Material style layer (Ink & Indigo on warm paper) in the current project.
argument-hint: "[--css-dest <path>] [--check]"
---

Install or update the shared MkDocs style layer in the current project, then
reconcile the project's `mkdocs.yml` with it.

## Arguments

`$ARGUMENTS`

- `--css-dest <path>` — where `custom.css` lands, relative to the project root.
  Only needed for non-standard layouts; see step 2.
- `--check` — report drift only: dry-run the installer and diff the vendored
  files against the payload. Make no changes.

## How the layer works

The canonical assets live in the claude-code-config repo under `tooling/mkdocs/`:
a partial parent config (`mkdocs.style.yml`: theme, features, palette, fonts,
markdown_extensions, `extra_css`, `extra.generator: false`) and the palette
stylesheet (`custom.css`). A project consumes them via MkDocs native config
inheritance — `INHERIT: mkdocs.style.yml` at the top of its `mkdocs.yml`.

MkDocs merges the child config **onto** the parent: mappings merge per-key
(child wins), but **lists replace wholesale**. So the project must not redefine
`theme.features`, `theme.palette`, `theme.font`, `markdown_extensions`, or
`extra_css` — unless it deliberately owns the whole list (and then `extra_css`
must still include `stylesheets/custom.css`). Per-project branding keys
(`theme.favicon`, `theme.logo`, `theme.icon.logo`) merge safely and stay in the
project.

## Steps

1. Resolve the config repo: `CONFIG_REPO="$(dirname "$(readlink ~/.claude/skills)")"`
   (the skills directory is a symlink into the repo). Run
   `git -C "$CONFIG_REPO" pull --ff-only` first so the payload is current.

2. Determine the css destination if `--css-dest` was not given:

   - Default: `docs/stylesheets/custom.css`.
   - Generated-docs projects (e.g. a `scripts/build-docs-tree.sh` that symlinks
     assets into a git-ignored `docs/`): use the committed source directory that
     is exposed as `stylesheets/` in the docs tree (career-portfolio:
     `mkdocs-theme/stylesheets/custom.css`).

3. Run the installer:
   `"$CONFIG_REPO/scripts/install-mkdocs-style.sh" --target . [--css-dest <path>]`
   (add `--dry-run` under `--check`, then also `diff` the two vendored files
   against the payload and report; stop here in check mode).

4. Reconcile `mkdocs.yml` — the judgment work the script only warns about:

   - Delete keys now owned by the parent: `theme.name`, `theme.features`,
     `theme.palette`, `theme.font`, `theme.icon.repo`, the whole
     `markdown_extensions` block, `extra_css` (unless the project needs extra
     stylesheets — then keep it as a deliberate whole-list override with
     `stylesheets/custom.css` first and a comment saying so), and
     `extra.generator`.
   - Keep: `INHERIT`, site metadata, plugins, nav, `extra.social`/`extra.tags`,
     validation, docs_dir/site_dir, dev_addr, and branding keys
     (`theme.favicon`, `theme.logo`, `theme.icon.logo`).
   - Delete any superseded palette CSS the project carried before.
   - Check logo/favicon contrast: the light header is warm paper (`#faf8f3`) —
     a white or very light logo asset becomes invisible. Prefer
     `theme.icon.logo` with a Material icon (inline SVG, `currentColor`, adapts
     to both schemes) over a fixed-colour image.
   - If the project's content might use `--8<--` literally, grep for it —
     `pymdownx.snippets` in the shared layer activates include syntax.

5. Verify:
   - Strict build via the project's own entry point (`make check`, `make ci`,
     `make docs-build`, or `uv run mkdocs build --strict`).
   - Spot-check the merged config:
     `uv run python -c "from mkdocs.config import load_config; c = load_config(); print(c['theme'].name, len(c['markdown_extensions']))"`
   - Show `git diff --stat` and summarise what changed visually (palette,
     features gained/lost) so the user can sign off.
