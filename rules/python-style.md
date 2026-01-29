---
paths:
  - "**/*.py"
---

# Python Style Rules

## General

- Functions: keep under 30 lines. Extract sub-functions if longer.
- Files: keep under 400 lines. Split into modules when growing beyond this.
- Nesting: maximum 3 levels of indentation. Use early returns to flatten logic.
- Comments: only where the "why" isn't obvious. Never restate what code does.

## Naming

- Functions and variables: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`
- Private: prefix with `_` (single underscore)
- Module-level dunder: `__all__`, `__version__`

## Error Handling

- Catch specific exceptions, never bare `except:`
- Use custom exception classes for domain errors
- Log exceptions with context before re-raising
- Use `raise ... from` for exception chaining

## Imports

- Standard library first, then third-party, then local
- Absolute imports preferred over relative
- No wildcard imports (`from module import *`)

## Type Hints

- All public function signatures must have type hints
- Use `from __future__ import annotations` for forward references
- Use `Optional[X]` explicitly instead of `X | None` for Python < 3.10
