#!/usr/bin/env python3
"""One-way sync of the repo's settings.json into ~/.claude/settings.json.

Why: ~/.claude/settings.json used to be a symlink into this repo, so every
user-scope runtime write (/model, /config toggles, permission approvals)
landed as a pending diff in a public repo — and the only file Claude Code
actually reads at user scope was the one it could not safely write to.
The sync replaces the symlink (ADR-0002): repo-managed keys mirror the
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

from lib.config_common import REPO_ROOT
from lib.settings_keys import ALLOWED_KEYS, RETIRED_KEYS


def merge(repo_cfg: dict, home_cfg: dict) -> tuple[dict, list[str]]:
    """Return (merged home config, human-readable change list)."""
    merged = dict(home_cfg)
    changes = []

    def render(value: object) -> str:
        text = json.dumps(value)
        return text if len(text) <= 60 else f"<{type(value).__name__} value>"

    managed = (ALLOWED_KEYS | set(repo_cfg) | RETIRED_KEYS) - {"enabledPlugins"}
    for key in sorted(managed):
        if key in repo_cfg and key not in RETIRED_KEYS:
            if key not in merged:
                changes.append(f"+ {key}: {render(repo_cfg[key])}")
            elif merged[key] != repo_cfg[key]:
                changes.append(f"~ {key}: {render(merged[key])} -> {render(repo_cfg[key])}")
            merged[key] = repo_cfg[key]
        elif key in merged:
            changes.append(f"- {key} (no longer managed by the repo)")
            del merged[key]

    repo_plugins = repo_cfg.get("enabledPlugins")
    if repo_plugins is None:
        if "enabledPlugins" in merged:
            changes.append("- enabledPlugins (no longer managed by the repo)")
            del merged["enabledPlugins"]
    else:
        plugins = dict(merged.get("enabledPlugins") or {})
        for name, value in sorted(repo_plugins.items()):
            if name not in plugins:
                changes.append(f"+ enabledPlugins.{name}: {render(value)}")
            elif plugins[name] != value:
                changes.append(
                    f"~ enabledPlugins.{name}: {render(plugins[name])} -> {render(value)}"
                )
            plugins[name] = value
        merged["enabledPlugins"] = plugins

    return merged, changes


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
    except BaseException:
        os.unlink(tmp)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(
        description="One-way sync of the repo's settings.json into ~/.claude/settings.json."
    )
    parser.add_argument("--check", action="store_true", help="warn-only drift report")
    parser.add_argument("--source-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--target", type=Path, default=Path.home() / ".claude" / "settings.json")
    args = parser.parse_args()

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
        # Backs the SessionStart drift hook: one line, warn-only, exit 0.
        if changes or was_symlink:
            keys = sorted({c.split()[1].rstrip(":").split(".")[0] for c in changes})
            what = ", ".join(keys) if keys else "symlinked target"
            print(
                f"claude-code-config: ~/.claude/settings.json has drifted from the"
                f" repo ({what}) — run scripts/setup-global.sh (or"
                f" scripts/sync-global-settings.py) to apply."
            )
        return 0

    if not changes and not was_symlink and target.exists():
        print(f"{target}: already in sync ({len(merged)} top-level keys).")
        return 0

    if was_symlink:
        print(f"Replacing symlink {target} -> {os.readlink(target)} with a real file.")
        target.unlink()
    target.parent.mkdir(parents=True, exist_ok=True)
    write_atomic(target, merged)

    for change in changes:
        print(f"  {change}")
    print(f"Synced {source} -> {target} ({len(changes)} change(s)).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
