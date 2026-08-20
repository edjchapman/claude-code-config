#!/usr/bin/env python3
"""One-way sync of the repo's settings.json into ~/.claude/settings.json.

Why: ~/.claude/settings.json used to be a symlink into this repo, so every
user-scope runtime write (/model, /config toggles, permission approvals)
landed as a pending diff in a public repo — and the only file Claude Code
actually reads at user scope was the one it could not safely write to.
The sync replaces the symlink (ADR-0002): managed keys mirror the
repo exactly; every other key in the home file is personal and is never
touched.

Semantics (strict mirror, one exception):

- Managed keys — ALLOWED_KEYS plus whatever the repo file carries — take
  the repo's value verbatim. A managed key the repo has dropped is deleted
  from the home file (RETIRED_KEYS tombstones cover keys retired from
  ALLOWED_KEYS itself). Both sets live in scripts/lib/settings_keys.py.
- ``enabledPlugins`` merges per entry: plugin entries the repo declares
  are mirrored exactly (default-offs stay off), entries the repo does not
  mention (personal, account-gated plugins) are preserved.
- Unmanaged keys (``model``, ``permissions``, future /config writes) are
  never touched.

A target that is still a symlink is replaced with a real merged file.

Usage:
  python3 scripts/sync-global-settings.py            # apply, print each change
  python3 scripts/sync-global-settings.py --check    # warn-only drift report
  python3 scripts/sync-global-settings.py --source-root DIR --target FILE

--check prints a one-line warning when a sync would change anything and
always exits 0 (it backs the warn-only SessionStart drift hook).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import NamedTuple

from lib.config_common import REPO_ROOT
from lib.settings_keys import ALLOWED_KEYS, RETIRED_KEYS


class Change(NamedTuple):
    """One sync mutation. ``key`` is the top-level settings key (the --check
    report groups by it, so plugin entries carry "enabledPlugins", not the
    entry name); ``line`` is the rendered human-readable description."""

    key: str
    line: str


def render(value: object) -> str:
    text = json.dumps(value)
    return text if len(text) <= 60 else f"<{type(value).__name__} value>"


def _mirror(mapping: dict, changes: list[Change], key: str, name: str, value: object) -> None:
    """Set mapping[name] to the repo's value, recording an add/update Change.

    ``name`` is the dict key being written; the Change carries the top-level
    ``key`` (identical to ``name`` except for plugin entries, where
    key="enabledPlugins" and the line shows "enabledPlugins.<name>").
    """
    label = name if key == name else f"{key}.{name}"
    if name not in mapping:
        changes.append(Change(key, f"+ {label}: {render(value)}"))
    elif mapping[name] != value:
        changes.append(Change(key, f"~ {label}: {render(mapping[name])} -> {render(value)}"))
    mapping[name] = value


def _drop(mapping: dict, changes: list[Change], key: str) -> None:
    """Delete a formerly-managed key, recording the removal."""
    changes.append(Change(key, f"- {key} (no longer managed by the repo)"))
    del mapping[key]


def merge(repo_cfg: dict, home_cfg: dict) -> tuple[dict, list[Change]]:
    """Return (merged home config, list of Changes applied)."""
    merged = dict(home_cfg)
    changes: list[Change] = []

    managed = (ALLOWED_KEYS | set(repo_cfg) | RETIRED_KEYS) - {"enabledPlugins"}
    for key in sorted(managed):
        if key in repo_cfg and key not in RETIRED_KEYS:
            _mirror(merged, changes, key, key, repo_cfg[key])
        elif key in merged:
            _drop(merged, changes, key)

    _merge_plugins(repo_cfg, merged, changes)
    return merged, changes


def _merge_plugins(repo_cfg: dict, merged: dict, changes: list[Change]) -> None:
    """Per-entry merge for enabledPlugins: repo entries mirror, others survive."""
    repo_plugins = repo_cfg.get("enabledPlugins")
    if repo_plugins is None:
        if "enabledPlugins" in merged:
            _drop(merged, changes, "enabledPlugins")
        return
    plugins = dict(merged.get("enabledPlugins") or {})
    for name, value in sorted(repo_plugins.items()):
        _mirror(plugins, changes, "enabledPlugins", name, value)
    merged["enabledPlugins"] = plugins


def load(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def write_atomic(path: Path, config: dict) -> None:
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=path.name + ".")
    try:
        with os.fdopen(fd, "w") as handle:
            json.dump(config, handle, indent=2)
            handle.write("\n")
        os.replace(tmp, path)
    finally:
        # os.replace consumed tmp on success; anything left is a failed write.
        if os.path.exists(tmp):
            os.unlink(tmp)


def report_drift(changes: list[Change], was_symlink: bool) -> None:
    """One-line warn-only drift report backing the SessionStart hook."""
    if not changes and not was_symlink:
        return
    keys = sorted({change.key for change in changes})
    what = ", ".join(keys) if keys else "symlinked target"
    print(
        f"claude-code-config: ~/.claude/settings.json has drifted from the"
        f" repo ({what}) — run scripts/setup-global.sh (or"
        f" scripts/sync-global-settings.py) to apply."
    )


def apply_sync(source: Path, target: Path, merged: dict, changes: list[Change]) -> None:
    if target.is_symlink():
        print(f"Replacing symlink {target} -> {os.readlink(target)} with a real file.")
        target.unlink()
    target.parent.mkdir(parents=True, exist_ok=True)
    write_atomic(target, merged)

    for change in changes:
        print(f"  {change.line}")
    print(f"Synced {source} -> {target} ({len(changes)} change(s)).")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="One-way sync of the repo's settings.json into ~/.claude/settings.json."
    )
    parser.add_argument("--check", action="store_true", help="warn-only drift report")
    parser.add_argument("--source-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--target", type=Path, default=Path.home() / ".claude" / "settings.json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source = args.source_root / "settings.json"
    if not source.is_file():
        print(f"FAIL: no settings.json at {args.source_root}", file=sys.stderr)
        return 1

    repo_cfg = json.loads(source.read_text())
    target: Path = args.target
    was_symlink = target.is_symlink()
    try:
        home_cfg = load(target)
    except json.JSONDecodeError as err:
        # Never clobber a file we cannot parse — surface it instead.
        message = f"claude-code-config: cannot parse {target} ({err}); not syncing."
        print(message if args.check else f"FAIL: {message}", file=sys.stderr)
        return 0 if args.check else 1
    merged, changes = merge(repo_cfg, home_cfg)

    if args.check:
        report_drift(changes, was_symlink)
        return 0
    if not changes and not was_symlink and target.exists():
        print(f"{target}: already in sync ({len(merged)} top-level keys).")
        return 0
    apply_sync(source, target, merged, changes)
    return 0


if __name__ == "__main__":
    sys.exit(main())
