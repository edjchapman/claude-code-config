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

Beyond the targets, this generator enforces the repo's declared invariants
(the first, second and fourth are CONTEXT.md glossary terms), every one a
named error rather than a stale doc:

  scheduling      a routine-fired skill stays model-invocable; a user-only
                  skill keeps its flag (lib/primitives.py).
  wired-coverage  every tracked scripts/hooks/*.sh is fired by a binding or
                  declared a non-hook (NON_HOOK_SCRIPTS, lib/primitives.py).
  documented      a wired event appears in the declared platform catalog
                  (DOCUMENTED_EVENTS, lib/architecture_catalogs.py), so the
                  "not wired" table stays the complement of the docs.
  no-count        hand-written prose in a markdown destination states no
                  primitive count (lib/prose_counts.py).
  plugin pin      settings.json's pin matches the committed lockfile
                  (lib/vendored_plugins.py), so a third-party primitive can
                  never change what it ships without a reviewed diff.

Primitives are enumerated from git-tracked files, so an untracked local-only
extra is never written into a catalog and staged by pre-commit.

settings.json is re-serialized canonically (json.dumps, indent=2, trailing
newline): every key outside the generated region keeps its value, but the
file's *formatting* is owned by this generator, not by hand edits or prettier
(settings.json is prettier-ignored for exactly this reason). Markdown
regions are marker-fenced spans replaced in place — every hand-written byte
outside them is preserved — and carry prettier-ignore fences so prettier
cannot re-pad the generated tables and lists.

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

from lib import architecture_catalogs, prose_counts, readme_catalogs, vendored_plugins
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


RegionBuilder = Callable[[Path], tuple[dict[str, str], list[str]]]


def _markdown_target(relative: str, build: RegionBuilder) -> Callable[[Path], dict[Path, str]]:
    """A target that splices `build`'s regions into one markdown destination.

    Every builder returns (regions, warnings): warnings go to stderr and
    never fail the run, and the spliced text — hand-written bytes intact —
    is then held to the no-count rule (lib/prose_counts.py).
    """

    def generate(root: Path) -> dict[Path, str]:
        destination = root / relative
        regions, warnings = build(root)
        for warning in warnings:
            print(f"warning: {warning}", file=sys.stderr)
        text = _splice(destination, regions)
        prose_counts.check_no_primitive_counts(destination, text)
        return {destination: text}

    return generate


TARGETS: dict[str, Callable[[Path], dict[Path, str]]] = {
    "settings-hooks": _generate_settings_hooks,
    "readme": _markdown_target("README.md", readme_catalogs.build_regions),
    "architecture": _markdown_target("docs/architecture.md", architecture_catalogs.build_regions),
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
    vendored_plugins.verify_pin(root)
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
