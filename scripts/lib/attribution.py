"""What counts as Claude attribution in a commit message or pull-request body.

settings.json's `attribution` key suppresses what the harness appends. It
has no authority over a trailer the model types, so a doc that tells the
model to add one, or a settings change that drops the key, brings
attribution back with no error anywhere (docs/architecture.md,
`attribution`). scripts/check-attribution.py runs these patterns over a
pull request so the regression is caught before merge.

Every pattern must match a whole line. Prose or inline code that mentions
a trailer — documentation about attribution, the pull request that changes
this check — is not attribution and must not match.
"""

from __future__ import annotations

import re

_PATTERNS = (
    # Matched on the address: the display name varies by model, the address
    # does not.
    re.compile(r"co-authored-by:.*<noreply@anthropic\.com>", re.IGNORECASE),
    # With or without the leading emoji and the markdown link.
    re.compile(
        r"(?:[^\x00-\x7f]+\s*)?generated with \[?claude code\]?(?:\([^)]*\))?", re.IGNORECASE
    ),
    re.compile(r"claude-session:\s*\S.*", re.IGNORECASE),
)


def find_attribution(text: str) -> list[tuple[int, str]]:
    """(line number, line) for every line of `text` that is Claude attribution."""
    hits = []
    for number, line in enumerate(text.splitlines(), start=1):
        candidate = line.rstrip()
        if any(pattern.fullmatch(candidate) for pattern in _PATTERNS):
            hits.append((number, candidate))
    return hits
