---
paths:
  - "**/*.tsx"
---

# React Style Rules

- Components: one per file, named same as file
- Props: define interface above component, suffix with `Props`
- Hooks: prefix custom hooks with `use`
- State: prefer derived state over synchronized state
- Effects: minimize `useEffect` -- prefer event handlers
