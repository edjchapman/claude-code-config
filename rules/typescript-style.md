---
paths:
  - "**/*.ts"
  - "**/*.tsx"
---

<!--
Only what a linter cannot say. If eslint or tsc flags it, it does not
belong here. Naming conventions were removed as derivable from the
language. These rules are user-level — they load in every TypeScript repo
on the machine, so nothing here may assume a framework. React guidance was
removed on that basis; if it returns it belongs in a skill, alongside
django-patterns, not in a language rule.
-->

# TypeScript Style

## Errors

- Model expected failures as discriminated unions; reserve try/catch for the exceptional.
- Never swallow an error silently.

## Types

- Prefer `interface` over `type` for object shapes.
- Use `unknown` over `any` — narrow with type guards.
- Mark data that shouldn't mutate `readonly`.
- Export types alongside their implementations.

## Files

- `kebab-case.ts` for modules.
