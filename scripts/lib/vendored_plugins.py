"""The third-party plugins this repo enables but does not own.

A **third-party primitive** (see CONTEXT.md) is a skill or agent shipped by an
external plugin. It costs always-loaded context exactly like a primitive this
repo ships, and it can collide with one — but it cannot be edited here, and it
lives outside the repo and outside CI.

Two consumers derive from this module, so the relationship is enforced rather
than remembered:

- ``generate.py --check`` fails when settings.json's pin drifts from the
  committed lockfile, so a plugin can never move without a reviewed diff.
- ``check-context-budget.py`` counts the pinned plugin's model-invocable
  descriptions into the always-loaded budget, so the reported number is the
  real per-session cost rather than only the part this repo authors.

The lockfile itself is produced by ``scripts/update-plugin-lock.py`` from the
local plugin cache. CI never regenerates it — CI only verifies it.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from .config_common import REPO_ROOT, GenerationError

# The lockfile for the one plugin this repo pins. Declared, not discovered:
# adopting a second vendored plugin is a deliberate act that costs a line here
# (the same posture ALLOWED_KEYS takes towards settings keys).
LOCKFILE = Path("plugins") / "mattpocock-skills.lock.json"
MARKETPLACE = "mattpocock"
PLUGIN = "mattpocock-skills"

PLUGIN_CACHE = Path.home() / ".claude" / "plugins" / "cache"

# A marketplace ref must be a branch or tag name: Claude Code clones a declared
# marketplace with `git clone --branch <ref>`, which git rejects for a SHA (#152).
SHA_LIKE = re.compile(r"[0-9a-f]{7,40}")


@dataclass(frozen=True)
class VendoredPlugin:
    """One third-party plugin as settings.json declares it."""

    marketplace: str
    name: str
    repo: str
    ref: str | None

    @classmethod
    def declared(cls, root: Path = REPO_ROOT) -> VendoredPlugin:
        """Read the declared plugin out of the repo's settings.json."""
        settings = json.loads((root / "settings.json").read_text())
        source = settings.get("extraKnownMarketplaces", {}).get(MARKETPLACE, {}).get("source", {})
        if not source.get("repo"):
            raise GenerationError(
                f"settings.json declares no extraKnownMarketplaces['{MARKETPLACE}'].source.repo, "
                f"but {LOCKFILE} pins it — remove the lockfile or restore the marketplace"
            )
        return cls(MARKETPLACE, PLUGIN, source["repo"], source.get("ref"))


def plugin_cache_root(plugin: VendoredPlugin) -> Path:
    """The installed plugin's directory in the local Claude Code cache.

    Local-only: the cache is a machine artifact, absent in CI. Callers that
    must work in CI read the lockfile instead.
    """
    parent = PLUGIN_CACHE / plugin.marketplace / plugin.name
    versions = sorted(path for path in parent.glob("*") if path.is_dir()) if parent.is_dir() else []
    if not versions:
        raise SystemExit(
            f"plugin not installed locally: {parent}\n"
            f"install it first (/plugin install {plugin.name}@{plugin.marketplace})"
        )
    return versions[-1]


def load_lock(root: Path = REPO_ROOT) -> dict | None:
    """The committed lockfile, or None when this repo pins nothing."""
    path = root / LOCKFILE
    if not path.is_file():
        return None
    return json.loads(path.read_text())


def verify_pin(root: Path = REPO_ROOT) -> None:
    """Fail when settings.json's pin and the lockfile disagree.

    The two can drift in either direction, and both are bugs: a moved pin with
    a stale lockfile means an unreviewed plugin reaches every session, while a
    regenerated lockfile with an unmoved pin means the review happened against
    something the config will not actually load.
    """
    lock = load_lock(root)
    if lock is None:
        return
    plugin = VendoredPlugin.declared(root)
    if plugin.ref is None:
        raise GenerationError(
            f"{LOCKFILE} pins {lock['ref']} but settings.json's "
            f"extraKnownMarketplaces['{MARKETPLACE}'].source has no `ref` — the marketplace "
            f"would track its default branch, and the lockfile would describe a state "
            f"this config never loads"
        )
    if SHA_LIKE.fullmatch(plugin.ref):
        raise GenerationError(
            f"settings.json pins extraKnownMarketplaces['{MARKETPLACE}'] to a commit SHA "
            f"({plugin.ref}); Claude Code installs a marketplace with `git clone --branch <ref>`, "
            f"which only accepts a branch or tag name, so a SHA pin cannot be installed from "
            f"scratch (#152). Pin a tag instead"
        )
    if plugin.ref != lock["ref"]:
        raise GenerationError(
            f"vendored plugin pin drift: settings.json pins {plugin.ref} but {LOCKFILE} "
            f"records {lock['ref']}. Regenerate the lockfile "
            f"(python3 scripts/update-plugin-lock.py) and read the diff — every changed "
            f"trigger is a collision candidate against this repo's own primitives"
        )


def always_loaded_items(root: Path = REPO_ROOT) -> list[tuple[str, int]]:
    """(label, description bytes) for each model-invocable skill the pin ships.

    These descriptions load into every session just like this repo's own, so
    the budget must see them. User-invocable skills carry no fixed cost and
    are deliberately excluded, mirroring how the repo's own skills are counted.
    """
    lock = load_lock(root)
    if lock is None:
        return []
    return [
        (f"{lock['plugin']}:{name} (description)", len(entry["description"].encode()))
        for name, entry in sorted(lock["skills"].items())
        if entry["model_invocable"]
    ]
