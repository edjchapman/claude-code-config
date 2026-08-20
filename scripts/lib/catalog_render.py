"""Markdown rendering helpers shared by the generator's catalog targets.

Pure formatting — nothing here touches disk. The README renders catalogs as
tables inside `<details>`; docs/architecture.md renders the same primitives
as reference bullet lists. Both go through these helpers so a region's
escaping and fencing rules are decided once.
"""

from __future__ import annotations


def escape(cell: str) -> str:
    """Escape table/emphasis metacharacters so verbatim text renders verbatim.

    `_` and `*` are escaped only outside code spans (backslashes would be
    literal inside backticks); escaping keeps glob-like prose such as
    `test_*` from being parsed — and reformatted — as emphasis.
    """
    parts = cell.replace("|", "\\|").split("`")
    for i in range(0, len(parts), 2):
        parts[i] = parts[i].replace("_", "\\_").replace("*", "\\*")
    return "`".join(parts)


def table(headers: list[str], rows: list[list[str]]) -> str:
    grid = [headers] + [[escape(cell) for cell in row] for row in rows]
    widths = [max(len(row[i]) for row in grid) for i in range(len(headers))]

    def render(row: list[str]) -> str:
        return "| " + " | ".join(c.ljust(w) for c, w in zip(row, widths)) + " |"

    separator = "| " + " | ".join("-" * w for w in widths) + " |"
    return "\n".join([render(grid[0]), separator] + [render(row) for row in grid[1:]])


def bullets(items: list[str]) -> str:
    """A markdown bullet list. Items are already-composed markdown, not cells.

    Unlike `table`, nothing is escaped: bullet text carries deliberate bold
    and code spans (a hook's `**Event**` label, a skill's `**schedulable**`
    marker) that the table escaper would defuse.
    """
    return "\n".join(f"- {item}" for item in items)


def details_body(summary: str, body: str) -> str:
    """Inner content of a <details> element; the tag itself is hand-written."""
    return f"<summary>{summary} — click to expand</summary>\n\n{body}"


def fence(content: str) -> str:
    """Wrap a region so prettier leaves the generator's formatting alone.

    Every blank line here is load-bearing. Each directive comment has to be
    its own HTML block for prettier to see it as a directive at all: without
    the leading blank it merges into the preceding block (`<details>` plus
    the BEGIN marker), and without the blanks around `content` a list or
    table butting against a comment swallows it — prettier then reformats
    the region it was told to leave alone, and re-indents the closing
    markers into the list.
    """
    return f"\n<!-- prettier-ignore-start -->\n\n{content}\n\n<!-- prettier-ignore-end -->"
