---
paths:
  - "**/*.py"
---

<!--
Only what a linter cannot say. If ruff (or any mainstream Python linter)
flags it, it does not belong here. Naming, import order and bare `except`
were removed for exactly that reason. These rules are user-level — they
load in every Python repo on the machine, so nothing here may assume a
particular linter config, framework or Python version.
-->

# Python Style

## Errors

- Define custom exception classes for domain errors; don't overload built-ins.
- Log exceptions with context before re-raising.

## Types and Imports

- Type-hint every public function signature.
- Prefer absolute imports over relative.
