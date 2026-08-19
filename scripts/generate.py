#!/usr/bin/env python3
"""Regenerate this repo's generated regions from their sources (ADR-0001).

A "generated region" is a span of a committed file owned by this generator;
hand edits inside one are reverted on the next run — the fix belongs in the
region's source. Targets registered here:

  settings-hooks  hooks/hooks.json 'hooks' -> settings.json 'hooks' key.
                  hooks/hooks.json is the source of truth for hook
                  definitions (docs/adr/0001-hooks-json-is-the-source-of-truth.md).

Destinations are re-serialized canonically (json.dumps, indent=2, trailing
newline); keys outside the generated region are preserved verbatim.

Usage: generate.py [--check] [--only TARGET] [--root PATH]

Write mode rewrites stale destinations. --check rewrites nothing and exits 1
if any destination is stale (wired into CI; pre-commit runs write mode).

Markdown targets (T2/T4 of the catalog-generation spec, issue #110) will fence
their regions with the markers below; replace_generated_region is their engine.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable
from pathlib import Path

from lib.config_common import check_python_version

REPO_ROOT = Path(__file__).resolve().parent.parent

MARKER_BEGIN = "<!-- BEGIN GENERATED: {name} -->"
MARKER_END = "<!-- END GENERATED: {name} -->"


class GenerationError(Exception):
    """A target's sources are missing or malformed."""


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


def _load_json(path: Path) -> dict:
    if not path.is_file():
        raise GenerationError(f"source not found: {path}")
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise GenerationError(f"invalid JSON in {path}: {exc}") from exc


def _canonical_json(obj: dict) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=False) + "\n"


def _generate_settings_hooks(root: Path) -> dict[Path, str]:
    """Splice hooks/hooks.json's 'hooks' into settings.json, preserving all else."""
    source = _load_json(root / "hooks" / "hooks.json")
    if "hooks" not in source:
        raise GenerationError(f"no 'hooks' key in {root / 'hooks' / 'hooks.json'}")
    destination = root / "settings.json"
    settings = _load_json(destination)
    settings["hooks"] = source["hooks"]
    return {destination: _canonical_json(settings)}


TARGETS: dict[str, Callable[[Path], dict[Path, str]]] = {
    "settings-hooks": _generate_settings_hooks,
}


def run(root: Path, check: bool, only: str | None) -> int:
    """Generate (or verify) every selected target; return the exit code."""
    names = [only] if only else list(TARGETS)
    stale: list[Path] = []
    for name in names:
        for path, content in TARGETS[name](root).items():
            current = path.read_text() if path.is_file() else None
            if current == content:
                continue
            stale.append(path)
            if check:
                print(f"stale: {path} (target '{name}' — run scripts/generate.py)")
            else:
                path.write_text(content)
                print(f"regenerated: {path} (target '{name}')")
    if check and stale:
        return 1
    if not stale:
        print("all generated regions up to date")
    return 0


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
