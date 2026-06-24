#!/usr/bin/env python3
"""Verify markdown link anchor fragments resolve to actual headings.

`scripts/check-links.sh` strips `#fragment` before validating link
targets, so a link like `[BIL-3721](evidence/jira-tickets.md#bil-3721)`
will pass even if the `#bil-3721` anchor doesn't exist on the target
file. The rebuild script emits ~100 auto-generated `#bil-NNNN` and
`#pr-NNNN` anchors that could silently drift on a renumber.

For each tracked `.md` file, parse `[text](path#fragment)` link
targets. For each target file, parse its `#` headings, slugify per
GitHub-Flavored-Markdown rules, and assert the link's fragment is in
the target's heading-slug set.

Slugify rules (matches what GFM does for headings rendered on
github.com — approximation, but verified against the existing repo's
auto-generated anchors):

  - Strip markdown formatting (`**`, `_`, `` ` ``)
  - Lowercase
  - Replace spaces with `-`
  - Strip everything not in `[a-z0-9_-]`
  - Deduplicate with `-1`, `-2`, etc. suffixes in document order

Excludes: external URLs (http/https/mailto/tel), and lines marked
`stale-anchor-allow` (mirrors the `stale-refs-allow` convention).

Run via `make check-anchors`. Wired into `make check` (hard-fail).
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
HEADING_RE = re.compile(r"^#+\s+(.+?)\s*$", re.MULTILINE)


def slugify_gfm(heading: str) -> str:
    """Approximate GitHub heading slug."""
    s = heading.lower().strip()
    # Strip common markdown formatting characters.
    s = re.sub(r"[*_`]", "", s)
    # Replace spaces with hyphens.
    s = s.replace(" ", "-")
    # Keep only ASCII alphanumeric, hyphen, underscore.
    s = re.sub(r"[^a-z0-9_-]", "", s)
    return s


def heading_slugs(text: str) -> set[str]:
    """Return the set of heading slugs in a markdown file."""
    seen: dict[str, int] = {}
    slugs: list[str] = []
    for h in HEADING_RE.findall(text):
        s = slugify_gfm(h)
        if not s:
            continue
        if s in seen:
            seen[s] += 1
            slugs.append(f"{s}-{seen[s]}")
        else:
            seen[s] = 0
            slugs.append(s)
    return set(slugs)


def is_external(target: str) -> bool:
    return target.startswith(("http://", "https://", "mailto:", "tel:"))


def main() -> int:
    repo_root = Path.cwd()
    # splitlines() + filter avoids the empty-repo trap: "".split("\n") == [""],
    # and Path("") resolves to "." (a directory) → IsADirectoryError on read.
    tracked = [
        line
        for line in subprocess.check_output(
            ["git", "ls-files", "*.md"], text=True
        ).splitlines()
        if line
    ]

    # Build heading-slug index once per file.
    slugs_by_file: dict[str, set[str]] = {}
    for rel in tracked:
        p = Path(rel)
        if not p.exists():
            continue
        slugs_by_file[rel] = heading_slugs(p.read_text())

    broken: list[tuple[str, int, str, str]] = []
    checked = 0

    for rel in tracked:
        p = Path(rel)
        if not p.exists():
            continue
        text = p.read_text()
        for lineno, line in enumerate(text.splitlines(), start=1):
            if "stale-anchor-allow" in line:
                continue
            for match in LINK_RE.finditer(line):
                target = match.group(1)
                if "#" not in target:
                    continue
                path_part, _, fragment = target.partition("#")
                if not fragment or is_external(path_part):
                    continue
                # Resolve relative path against the source file's directory.
                if path_part:
                    target_path = (p.parent / path_part).resolve()
                    try:
                        target_rel = str(target_path.relative_to(repo_root))
                    except ValueError:
                        # Outside repo — skip (link check handles file-level).
                        continue
                else:
                    target_rel = rel  # same-file anchor
                if target_rel not in slugs_by_file:
                    # Target file isn't tracked or doesn't exist — let
                    # check-links surface that as a file-level miss.
                    continue
                checked += 1
                if fragment not in slugs_by_file[target_rel]:
                    broken.append((rel, lineno, fragment, target_rel))

    if broken:
        print(f"FAIL: {len(broken)} broken anchor fragment(s) of {checked} checked:")
        for src, lineno, frag, tgt in broken:
            print(f"  {src}:{lineno} → {tgt}#{frag}")
        print()
        print("  Headings on the target file don't contain a slug matching the fragment.")
        print("  Either fix the fragment to match the heading slug, or add `stale-anchor-allow`")
        print("  on the link line if the broken reference is intentional.")
        return 1

    print(f"OK: all {checked} anchor fragments resolve")
    return 0


if __name__ == "__main__":
    sys.exit(main())
