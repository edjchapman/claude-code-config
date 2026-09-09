"""The no-count rule, asserted: hand-written prose states no primitive count.

Every count of primitives the docs carry is rendered by the generator
(issue #114's acceptance criterion). A count typed into hand-written prose
is right the day it is written and wrong the day the catalog changes, with
nothing to notice — so the catalog-bearing docs are scanned, outside their
generated regions, for a sentence that states one, and a hit fails the run
naming the file and line.

Scope is deliberately the glossary term *primitive* (CONTEXT.md): a number
followed by a primitive noun ("4 skills", "two cloud routines"), or the
shape that refers back to an enumeration just given ("all three are
opt-in", "these five weren't earning"). Architectural facts — "two install
modes", "one canonical config" — do not trip it. Fenced code blocks and
inline code spans are skipped: a version, a byte budget, or a `4.` in a
numbered shell comment is not a claim about the catalog.
"""

from __future__ import annotations

import re
from pathlib import Path

from lib.config_common import GenerationError

_NUMBER = r"(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|dozen)"
_PRIMITIVE = (
    r"(?:agents?|skills?|hooks?|rules?|templates?|scripts?|routines?|plugins?|bindings?|"
    r"primitives?|output styles?)"
)
# "4 skills", "two cloud routines", "three opt-in prompt hooks".
_COUNTED_PRIMITIVE = re.compile(
    rf"(?<![\w`$.-]){_NUMBER}\s+(?:[a-z-]+\s+){{0,2}}{_PRIMITIVE}\b(?!-)", re.IGNORECASE
)
# "all three are opt-in", "these five weren't earning" — a bare number that
# only makes sense as a reference back to a list the reader was just shown.
_BACK_REFERENCE = re.compile(
    rf"\b(?:all|these|those)\s+{_NUMBER}\s+(?:are|were|weren't|aren't|is|was|isn't|wasn't)\b",
    re.IGNORECASE,
)
_GENERATED_REGION = re.compile(
    r"<!-- BEGIN GENERATED: (\S+) -->.*?<!-- END GENERATED: \1 -->", re.DOTALL
)


def _hand_written_lines(text: str) -> list[tuple[int, str]]:
    """(line number, line) for every prose line outside generated regions and code."""
    # Blank the regions rather than cut them so line numbers stay true.
    text = _GENERATED_REGION.sub(lambda m: "\n" * m.group(0).count("\n"), text)
    lines = []
    in_fence = False
    for number, line in enumerate(text.splitlines(), start=1):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if not in_fence:
            lines.append((number, re.sub(r"`[^`]*`", "``", line)))
    return lines


def check_no_primitive_counts(path: Path, text: str) -> None:
    """Raise GenerationError naming the first hand-written primitive count in `text`."""
    for number, line in _hand_written_lines(text):
        match = _COUNTED_PRIMITIVE.search(line) or _BACK_REFERENCE.search(line)
        if match:
            raise GenerationError(
                f"{path.name}:{number}: hand-written prose states a primitive count "
                f"({match.group(0)!r}) — counts are generated, so derive it or drop it"
            )
