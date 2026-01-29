---
paths:
  - "**/*.ts"
  - "**/*.tsx"
---

# TypeScript Style Rules

## General

- Functions: keep under 30 lines. Extract sub-functions if longer.
- Files: keep under 400 lines. Split into modules when growing beyond this.
- Nesting: maximum 3 levels of indentation. Use early returns to flatten logic.
- Comments: only where the "why" isn't obvious. Never restate what code does.

## Naming

- Variables and functions: `camelCase`
- Classes and interfaces: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`
- Type parameters: single capital letter (`T`, `K`, `V`)
- Files: `kebab-case.ts` for utilities, `PascalCase.tsx` for React components

## Error Handling

- Never swallow errors silently in catch blocks
- Use discriminated unions for expected failure cases
- Reserve try/catch for truly exceptional situations
- Always type error responses in API handlers

## Types

- Prefer `interface` over `type` for object shapes
- Use `unknown` instead of `any` -- narrow with type guards
- Export types alongside their implementations
- Use `readonly` for data that shouldn't mutate
