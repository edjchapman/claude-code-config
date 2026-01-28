---
name: coding-standards
description: Enforces naming conventions, function length limits, and error handling patterns across Python and TypeScript codebases.
globs:
  - "**/*.py"
  - "**/*.ts"
  - "**/*.tsx"
---

# Coding Standards

Apply these standards when writing or reviewing code in this project.

## General Principles

- **Functions**: Keep under 30 lines. If longer, extract sub-functions.
- **Files**: Keep under 400 lines. Split into modules when growing beyond this.
- **Nesting**: Maximum 3 levels of indentation. Use early returns to flatten logic.
- **Comments**: Only where the "why" isn't obvious. Never restate what code does.

## Python Standards

### Naming
- Functions and variables: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`
- Private: prefix with `_` (single underscore)
- Module-level dunder: `__all__`, `__version__`

### Error Handling
- Catch specific exceptions, never bare `except:`
- Use custom exception classes for domain errors
- Log exceptions with context before re-raising
- Use `raise ... from` for exception chaining

### Imports
- Standard library first, then third-party, then local
- Absolute imports preferred over relative
- No wildcard imports (`from module import *`)

### Type Hints
- All public function signatures must have type hints
- Use `from __future__ import annotations` for forward references
- Use `Optional[X]` explicitly instead of `X | None` for Python < 3.10

## TypeScript Standards

### Naming
- Variables and functions: `camelCase`
- Classes and interfaces: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`
- Type parameters: single capital letter (`T`, `K`, `V`)
- Files: `kebab-case.ts` for utilities, `PascalCase.tsx` for React components

### Error Handling
- Never swallow errors silently in catch blocks
- Use discriminated unions for expected failure cases
- Reserve try/catch for truly exceptional situations
- Always type error responses in API handlers

### Types
- Prefer `interface` over `type` for object shapes
- Use `unknown` instead of `any` -- narrow with type guards
- Export types alongside their implementations
- Use `readonly` for data that shouldn't mutate

## React Standards (when applicable)

- Components: one per file, named same as file
- Props: define interface above component, suffix with `Props`
- Hooks: prefix custom hooks with `use`
- State: prefer derived state over synchronized state
- Effects: minimize `useEffect` -- prefer event handlers
