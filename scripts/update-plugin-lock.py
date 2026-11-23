#!/usr/bin/env python3
# Regenerate the vendored-plugin lockfile from the local plugin cache.
#
# Why: a third-party primitive costs always-loaded context and can collide
# with a primitive this repo owns, but its source lives outside the repo and
# outside CI. The lockfile is the committed, reviewable record of what a
# pinned plugin actually ships; regenerating it turns an upstream change into
# a diff you must read before it reaches a session.
#
# This script needs the plugin installed locally (it reads ~/.claude/plugins),
# so it is a local-only tool. CI never runs it — CI only verifies that
# settings.json's pin still matches the committed lockfile.
#
# The pin is a tag, which upstream can re-cut, so the lockfile also records
# the commit the tag resolved to, read from the local marketplace clone.
# scripts/check-plugin-drift.py compares the clone with it from then on.
#
# Usage: python3 scripts/update-plugin-lock.py [--ref REF] [--root PATH]
#
# Bumping a pin is a three-step, reviewed act:
#   1. move the pin in settings.json and refresh the local plugin (the ordered
#      procedure is in docs/extending.md, "Bumping a vendored plugin")
#   2. python3 scripts/update-plugin-lock.py --ref <new ref>
#   3. read the lockfile diff — every changed trigger is a collision candidate
#      against this repo's own primitives (see docs/extending.md)

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib.config_common import REPO_ROOT, check_python_version  # noqa: E402
from lib.vendored_plugins import (  # noqa: E402
    LOCKFILE,
    MARKETPLACE_CLONES,
    PLUGIN_CACHE,
    VendoredPlugin,
    clone_commit,
    plugin_cache_root,
)

# A ref that names a release: `v1.2.3` or `1.2.3`. Anything else (a branch)
# cannot be compared with the cached plugin's version.
VERSION_REF = re.compile(r"v?(\d+(?:\.\d+)+)")


def _skill_manifest(cache: Path) -> dict[str, dict]:
    """Every skill the plugin's own manifest whitelists, with its trigger.

    A plugin ships only the skills its `.claude-plugin/plugin.json` lists —
    the repo may contain many more. Walking the manifest rather than the
    skills directory records what actually reaches a session.
    """
    manifest = json.loads((cache / ".claude-plugin" / "plugin.json").read_text())
    entries: dict[str, dict] = {}
    for relative in manifest["skills"]:
        path = cache / relative.lstrip("./") / "SKILL.md"
        text = path.read_text()
        match = re.search(r"^description: *(.+)$", text, re.M)
        if not match:
            raise SystemExit(f"no description: frontmatter in {path}")
        entries[path.parent.name] = {
            "description": match.group(1).strip().strip('"'),
            "model_invocable": not re.search(r"^disable-model-invocation: *true", text, re.M),
        }
    return entries


def main() -> None:
    check_python_version()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--ref", help="the tag (or branch) to record as the pin — never a commit SHA (#152)"
    )
    parser.add_argument("--root", type=Path, default=REPO_ROOT)
    parser.add_argument(
        "--cache", type=Path, default=PLUGIN_CACHE, help="plugin cache override (tests)"
    )
    parser.add_argument(
        "--marketplaces",
        type=Path,
        default=MARKETPLACE_CLONES,
        help="marketplace clones directory override (tests)",
    )
    args = parser.parse_args()

    plugin = VendoredPlugin.declared()
    cache = plugin_cache_root(plugin, args.cache)
    skills = _skill_manifest(cache)
    version = json.loads((cache / ".claude-plugin" / "plugin.json").read_text())["version"]

    ref = args.ref or plugin.ref
    if not ref:
        raise SystemExit("no --ref given and no pin in settings.json to inherit")

    # A lockfile stamped with one ref but read from another cached version
    # passes verify_pin (which compares refs only) while describing content
    # the pin does not load (#155).
    named = VERSION_REF.fullmatch(ref)
    if named and named.group(1) != version:
        raise SystemExit(
            f"ref {ref} names version {named.group(1)}, but the newest cached plugin "
            f"({cache}) is version {version} — nothing written.\n"
            f"Refresh the local plugin so the cache holds {ref}, then rerun "
            f'(docs/extending.md, "Bumping a vendored plugin").'
        )
    if not named:
        print(
            f"note: ref {ref} is not version-shaped — version not verified against "
            f"the cached plugin ({version})"
        )

    # The commit is the reviewed baseline the drift check compares against,
    # so it is only recorded from a clone that is sitting on the ref (#156).
    clone = args.marketplaces / plugin.marketplace
    commit = clone_commit(clone)
    if commit is None:
        raise SystemExit(
            f"no marketplace clone at {clone}, so the commit {ref} resolves to cannot "
            f"be recorded — nothing written.\n"
            f"Add the marketplace first (claude plugin marketplace update {plugin.marketplace})."
        )
    resolved = clone_commit(clone, ref)
    if resolved != commit:
        raise SystemExit(
            f"marketplace clone {clone} is at {commit}, but {ref} resolves to "
            f"{resolved or 'nothing'} there — nothing written.\n"
            f"Refresh the clone so it sits on {ref}, then rerun "
            f'(docs/extending.md, "Bumping a vendored plugin").'
        )

    always_loaded = sum(
        len(entry["description"].encode()) for entry in skills.values() if entry["model_invocable"]
    )
    lock = {
        "_comment": (
            "Generated by scripts/update-plugin-lock.py — do not hand-edit. "
            "The committed record of what the pinned third-party plugin ships. "
            "settings.json's pin must match `ref`; CI enforces it."
        ),
        "marketplace": plugin.marketplace,
        "plugin": plugin.name,
        "repo": plugin.repo,
        "ref": ref,
        "commit": commit,
        "version": version,
        "always_loaded_bytes": always_loaded,
        "skills": dict(sorted(skills.items())),
    }

    destination = args.root / LOCKFILE
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(lock, indent=2, ensure_ascii=False) + "\n")

    auto = sum(1 for entry in skills.values() if entry["model_invocable"])
    print(f"wrote {destination.relative_to(args.root)}")
    print(f"  ref     {ref}")
    print(f"  commit  {commit}")
    print(f"  version {version}")
    print(
        f"  skills  {len(skills)} shipped, {auto} model-invocable, {always_loaded} B always-loaded"
    )


if __name__ == "__main__":
    main()
