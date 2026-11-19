#!/usr/bin/env python3
"""Fail a pull request whose commit messages or body carry Claude attribution.

Reads the pull_request event payload GitHub Actions writes to
$GITHUB_EVENT_PATH: the body, and the base and head commits. Only the
commits the pull request adds (base..head) are scanned; history already on
the base branch is not this check's concern. The body is read from the
payload file and never passes through a shell.

What counts as attribution is defined in lib/attribution.py.

Usage: python3 scripts/check-attribution.py --event "$GITHUB_EVENT_PATH"
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from lib.attribution import find_attribution


def added_commits(base: str, head: str) -> list[tuple[str, str]]:
    """(sha, full message) for each commit in base..head, oldest first."""
    log = subprocess.run(
        ["git", "log", "-z", "--reverse", "--format=%H%n%B", f"{base}..{head}"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    commits = []
    for record in filter(None, log.split("\0")):
        sha, _, message = record.partition("\n")
        commits.append((sha, message))
    return commits


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--event", type=Path, required=True, help="path to the pull_request event payload (JSON)"
    )
    args = parser.parse_args()

    pull_request = json.loads(args.event.read_text()).get("pull_request")
    if not pull_request:
        print(f"ERROR: {args.event} is not a pull_request event payload.")
        return 2

    commits = added_commits(pull_request["base"]["sha"], pull_request["head"]["sha"])
    findings = []
    for sha, message in commits:
        subject = message.splitlines()[0] if message.strip() else "(no subject)"
        for number, line in find_attribution(message):
            findings.append(f"commit {sha[:12]} ({subject}), line {number}: {line}")
    for number, line in find_attribution(pull_request.get("body") or ""):
        findings.append(f"PR body, line {number}: {line}")

    if not findings:
        noun = "commit" if len(commits) == 1 else "commits"
        print(f"Attribution check OK ({len(commits)} {noun} and the PR body scanned).")
        return 0

    print("FAIL: Claude attribution found. This repo's commits and pull requests carry none.")
    for finding in findings:
        print(f"  {finding}")
    print("Reword the commit or edit the PR description to remove the line.")
    print("If a doc or instruction told the model to add it, fix that too:")
    print("see the `attribution` entry in docs/architecture.md.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
