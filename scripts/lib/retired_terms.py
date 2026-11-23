"""The retired-terms tripwire: a renamed term must not survive in a living doc.

`generate.py --check` owns the catalogs, but the prose describing how the
system works is hand-written, so a rename can land while a doc elsewhere
keeps the old vocabulary (issue #132). The glossary already records each
rename: an entry may carry a _formerly "…"_ alias naming its retired term.
This module derives the retired terms from those aliases — there is no
second list — and fails the run when one appears in a living doc.

Living docs are the root CLAUDE.md, the README, docs/ outside docs/adr/,
the skills and agents trees, and the header of every script under scripts/.
Two files are exempt by design: the glossary, which holds every retired term
inside the alias that declares it, and docs/adr/, whose records keep their
point-in-time wording.

It catches renames only. Prose that is wrong without using a retired term
is out of its reach.
"""

from __future__ import annotations

import re
from pathlib import Path

from lib.config_common import GenerationError, tracked_files

GLOSSARY = "CONTEXT.md"

_ENTRY = re.compile(r"^- \*\*(.+?)\*\*", re.MULTILINE)
# _Formerly "x"_ and _Formerly described as "x"_, matched after an entry's
# whitespace is collapsed: an alias may wrap between `Formerly` and its term.
#
# Not `\b`: the aliases are italic, and the `_` that opens `_Formerly` is a
# word character, so a word boundary never matches there.
_WORD = r"(?<![A-Za-z])formerly(?![A-Za-z])"
_ALIAS = re.compile(_WORD + r"(?: described as)? [\"“]([^\"”]+)[\"”]", re.IGNORECASE)
_FORMERLY = re.compile(_WORD, re.IGNORECASE)

# What may sit between two words of a term that wraps across lines: the
# break itself plus a comment, quote or list marker opening the next line.
_WRAP = r"[\s#>*]+"


def parse_retired_terms(glossary: str) -> dict[str, str]:
    """{retired term: the glossary entry that declares it}.

    Raises when an entry says "formerly" in a shape the alias grammar does
    not parse. Without that, a rephrased alias would drop out of the check
    while the check went on passing.
    """
    terms: dict[str, str] = {}
    starts = list(_ENTRY.finditer(glossary))
    for index, start in enumerate(starts):
        end = starts[index + 1].start() if index + 1 < len(starts) else len(glossary)
        body = " ".join(glossary[start.start() : end].split())
        aliases = _ALIAS.findall(body)
        if len(aliases) != len(_FORMERLY.findall(body)):
            raise GenerationError(
                f"{GLOSSARY}: the **{start.group(1)}** entry says 'formerly' without a quoted "
                f'retired term the tripwire can parse — write it as _Formerly "old term"_ '
                f'or _Formerly described as "old term"_'
            )
        for alias in aliases:
            terms[alias] = start.group(1)
    return terms


def _script_header(text: str) -> str:
    """`text` with everything below the script's header blanked out.

    The header is the leading `#` block, then a Python module docstring if
    one follows. Blanking instead of cutting keeps line numbers true.
    """
    lines = text.splitlines()
    end = 0
    while end < len(lines) and (lines[end].startswith("#") or not lines[end].strip()):
        end += 1
    if end < len(lines) and lines[end].startswith(('"""', "'''")):
        quote = lines[end][:3]
        closed = lines[end].count(quote) >= 2
        end += 1
        while not closed and end < len(lines):
            closed = quote in lines[end]
            end += 1
    return "\n".join(lines[:end])


def _living_docs(root: Path) -> list[tuple[Path, bool]]:
    """(path, header only?) for every tracked living doc under `root`."""
    whole = [
        path
        for pattern in (":(glob)CLAUDE.md", ":(glob)README.md", "docs/*.md", "skills", "agents")
        for path in tracked_files(pattern, root)
        if (root / "docs" / "adr") not in path.parents
    ]
    headers = tracked_files("scripts/*.sh", root) + tracked_files("scripts/*.py", root)
    return [(path, False) for path in whole] + [(path, True) for path in headers]


def check_no_retired_terms(root: Path) -> None:
    """Raise GenerationError listing every retired term found in a living doc."""
    glossary = root / GLOSSARY
    if not glossary.is_file():
        return
    terms = parse_retired_terms(glossary.read_text())
    patterns = {
        term: re.compile(
            rf"(?<![\w-]){_WRAP.join(map(re.escape, term.split()))}(?![\w-])", re.IGNORECASE
        )
        for term in terms
    }
    hits: list[tuple[str, int, str]] = []
    for path, header_only in _living_docs(root):
        try:
            text = path.read_text()
        except UnicodeDecodeError:
            continue
        if header_only:
            text = _script_header(text)
        for term, pattern in patterns.items():
            for match in pattern.finditer(text):
                line = text.count("\n", 0, match.start()) + 1
                hits.append((str(path.relative_to(root)), line, term))
    if hits:
        raise GenerationError(
            "retired term in a living doc:\n"
            + "\n".join(
                f'  {relative}:{line}: "{term}" was retired — {GLOSSARY}\'s '
                f"**{terms[term]}** entry has the current wording"
                for relative, line, term in sorted(hits)
            )
        )
