#!/usr/bin/env python3
"""Regenerate this repo's generated regions from their sources (ADR-0001).

A "generated region" is a span of a committed file owned by this generator;
hand edits inside one are reverted on the next run — the fix belongs in the
region's source. Targets registered here:

  settings-hooks  hooks/hooks.json 'hooks' -> settings.json 'hooks' key.
                  hooks/hooks.json is the source of truth for hook
                  definitions (docs/adr/0001-hooks-json-is-the-source-of-truth.md).
  readme          The README's catalog regions (tables, counts, directory
                  tree), rendered from the primitives on disk by
                  lib/readme_catalogs.py (issue #112). Skills the hand-written
                  "I want to…" cheat-sheet never mentions get a soft warning
                  on stderr — never a failure.
  architecture    docs/architecture.md's reference regions, rendered by
                  lib/architecture_catalogs.py (issue #114): the same
                  primitives as the README plus the two *difference* lists —
                  documented-but-unwired hook events, documented-but-unset
                  settings keys — that keep the doc from claiming the repo
                  lacks something it now has.

settings.json is re-serialized canonically (json.dumps, indent=2, trailing
newline): every key outside the generated region keeps its value, but the
file's *formatting* is owned by this generator, not by hand edits or prettier
(settings.json is prettier-ignored for exactly this reason). README regions
are marker-fenced spans replaced in place — every hand-written byte outside
them is preserved — and carry prettier-ignore fences so prettier cannot
re-pad the generated tables.

Usage: generate.py [--check] [--only TARGET] [--root PATH]

Write mode rewrites stale destinations. --check rewrites nothing and exits 1
if any destination is stale (wired into CI; pre-commit runs write mode).
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable
from pathlib import Path

from lib import architecture_catalogs, readme_catalogs
from lib.config_common import GenerationError, check_python_version, load_json

REPO_ROOT = Path(__file__).resolve().parent.parent

MARKER_BEGIN = "<!-- BEGIN GENERATED: {name} -->"
MARKER_END = "<!-- END GENERATED: {name} -->"


def replace_generated_region(text: str, name: str, content: str) -> str:
    """Replace the marker-fenced region `name` in `text` with `content`."""
    begin = MARKER_BEGIN.format(name=name)
    end = MARKER_END.format(name=name)
    try:
        head, rest = text.split(begin, 1)
        _, tail = rest.split(end, 1)
    except ValueError as exc:
        raise GenerationError(f"generated region '{name}' markers not found") from exc
    return f"{head}{begin}\n{content}\n{end}{tail}"


def _canonical_json(obj: dict) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=False) + "\n"


def _generate_settings_hooks(root: Path) -> dict[Path, str]:
    """Splice hooks/hooks.json's 'hooks' into settings.json, preserving all else."""
    source = load_json(root / "hooks" / "hooks.json")
    if "hooks" not in source:
        raise GenerationError(f"no 'hooks' key in {root / 'hooks' / 'hooks.json'}")
    destination = root / "settings.json"
    settings = load_json(destination)
    settings["hooks"] = source["hooks"]
    return {destination: _canonical_json(settings)}


def _splice(destination: Path, regions: dict[str, str]) -> str:
    """Replace every named region in `destination`; all other bytes survive."""
    if not destination.is_file():
        raise GenerationError(f"destination not found: {destination}")
    text = destination.read_text()
    for name, content in regions.items():
        text = replace_generated_region(text, name, content)
    return text


def _generate_readme(root: Path) -> dict[Path, str]:
    """Replace every catalog region in README.md; all other bytes survive."""
    destination = root / "README.md"
    regions, skill_names = readme_catalogs.build_regions(root)
    text = _splice(destination, regions)
    for warning in readme_catalogs.uncurated_skills(text, skill_names):
        print(f"warning: {warning}", file=sys.stderr)
    return {destination: text}


def _generate_architecture(root: Path) -> dict[Path, str]:
    """Replace every reference region in docs/architecture.md (issue #114)."""
    destination = root / "docs" / "architecture.md"
    regions, warnings = architecture_catalogs.build_regions(root)
    for warning in warnings:
        print(f"warning: {warning}", file=sys.stderr)
    return {destination: _splice(destination, regions)}


TARGETS: dict[str, Callable[[Path], dict[Path, str]]] = {
    "settings-hooks": _generate_settings_hooks,
    "readme": _generate_readme,
    "architecture": _generate_architecture,
}


def _sync_path(name: str, path: Path, content: str, check: bool) -> bool:
    """Bring one destination up to date (or just report it); True if it was stale."""
    current = path.read_text() if path.is_file() else None
    if current == content:
        return False
    if check:
        print(f"stale: {path} (target '{name}' — run scripts/generate.py)")
    else:
        path.write_text(content)
        print(f"regenerated: {path} (target '{name}')")
    return True


def run(root: Path, check: bool, only: str | None) -> int:
    """Generate (or verify) every selected target; return the exit code."""
    names = [only] if only else list(TARGETS)
    stale = False
    for name in names:
        for path, content in TARGETS[name](root).items():
            stale = _sync_path(name, path, content, check) or stale
    if not stale:
        print("all generated regions up to date")
    return 1 if (check and stale) else 0


def main() -> None:
    check_python_version()
    parser = argparse.ArgumentParser(
        description="Regenerate this repo's generated regions from their sources (ADR-0001)."
    )
    parser.add_argument("--check", action="store_true", help="verify only; exit 1 if stale")
    parser.add_argument("--only", choices=sorted(TARGETS), help="run a single target")
    parser.add_argument("--root", type=Path, default=REPO_ROOT, help="repo root override")
    args = parser.parse_args()
    try:
        sys.exit(run(args.root, args.check, args.only))
    except GenerationError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
