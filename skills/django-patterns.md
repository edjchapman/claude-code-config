---
name: django-patterns
description: Django architecture patterns including fat models, custom managers, query optimization, signals, and migration best practices.
globs:
  - "**/models.py"
  - "**/views.py"
  - "**/serializers.py"
  - "**/admin.py"
  - "**/managers.py"
  - "**/signals.py"
---

# Django Patterns

## Fat Models, Thin Views

- Put business logic in model methods, not views
- Views should handle HTTP concerns only: parse request, call model/service, return response
- Use model methods for validation, state transitions, and computed properties
- Use `@property` for derived attributes that don't need arguments

## Custom Managers and QuerySets

- Use custom managers for reusable query logic (`objects = MyManager()`)
- Define custom QuerySet classes and use `as_manager()` for chainable filters
- Common patterns: `active()`, `for_user(user)`, `with_related()`
- Never put raw SQL in views -- encapsulate in manager methods

## Query Optimization

- Always use `select_related()` for ForeignKey/OneToOne joins
- Always use `prefetch_related()` for ManyToMany/reverse FK
- Use `only()` / `defer()` to limit fetched columns when appropriate
- Use `values()` / `values_list()` for read-only aggregation queries
- Watch for N+1 queries in serializers and templates
- Use `django-debug-toolbar` or `EXPLAIN` to verify query plans

## Signals

- Avoid signals for business logic -- prefer explicit method calls
- Acceptable uses: audit logging, cache invalidation, denormalization
- Always use `dispatch_uid` to prevent duplicate registration
- Keep signal handlers small and fast -- offload heavy work to tasks
- Document which signals exist and what they do

## Migration Patterns

- One migration per logical change -- don't combine unrelated changes
- Use `RunPython` with both forward and reverse functions
- For large tables, consider batched data migrations
- Always test migrations with `--plan` before applying
- Use `AddIndex` / `RemoveIndex` separately from schema changes for zero-downtime
- Name migrations descriptively: `0042_add_user_email_verified_field`

## Admin Configuration

- Register all models with at least `list_display` and `search_fields`
- Use `list_select_related` to avoid N+1 in admin list views
- Use `raw_id_fields` for ForeignKey fields with many options
- Add `readonly_fields` for computed or audit fields
