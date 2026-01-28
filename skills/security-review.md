---
name: security-review
description: Input validation, parameterized queries, JWT rules, CSRF, and authentication security patterns.
globs:
  - "**/auth/**"
  - "**/authentication/**"
  - "**/middleware/**"
  - "**/security/**"
  - "**/views/**"
  - "**/api/**"
  - "**/routes/**"
---

# Security Review

Apply these security practices when writing or reviewing code in auth, middleware, and API layers.

## Input Validation

- **Always validate** at system boundaries (API endpoints, form handlers, message consumers)
- **Never trust** client-side validation alone
- Use allowlists over denylists for input filtering
- Validate types, lengths, ranges, and formats
- Sanitize HTML output to prevent XSS (use framework auto-escaping)

## SQL Injection Prevention

- **Always** use parameterized queries or ORM methods
- **Never** construct SQL with string concatenation or f-strings
- Django: use QuerySet methods, `Q` objects, or `params` argument for raw SQL
- Node.js: use query builders (Knex) or ORM (Prisma, TypeORM) -- never template literals in SQL

```python
# WRONG
User.objects.raw(f"SELECT * FROM users WHERE email = '{email}'")

# CORRECT
User.objects.raw("SELECT * FROM users WHERE email = %s", [email])
User.objects.filter(email=email)
```

## Authentication

- Hash passwords with bcrypt, argon2, or scrypt (never MD5/SHA alone)
- Enforce minimum password complexity at registration
- Rate-limit login attempts (exponential backoff or account lockout)
- Use constant-time comparison for tokens and secrets
- Invalidate sessions on password change

## JWT / Token Security

- Set short expiration times (15min for access tokens, days for refresh)
- Store refresh tokens server-side (database or Redis)
- Never store sensitive data in JWT payload (it's base64, not encrypted)
- Validate `iss`, `aud`, and `exp` claims on every request
- Use `RS256` or `ES256` over `HS256` for multi-service architectures

## CSRF Protection

- Enable framework CSRF middleware (Django: `CsrfViewMiddleware`)
- Use `SameSite=Lax` or `Strict` on session cookies
- For SPAs: use token-based auth or double-submit cookies
- Never disable CSRF protection for convenience

## Authorization

- Check permissions on every request, not just in UI
- Use role-based or attribute-based access control
- Verify object ownership: `if obj.owner != request.user: return 403`
- Log authorization failures for monitoring

## Secrets Management

- Never hardcode secrets, API keys, or passwords in code
- Use environment variables or secret managers (AWS Secrets Manager, Vault)
- Add `.env` and credential files to `.gitignore`
- Rotate secrets on schedule and after any suspected breach

## HTTP Security Headers

Ensure these headers are set in production:

- `Strict-Transport-Security: max-age=31536000; includeSubDomains`
- `Content-Security-Policy: default-src 'self'`
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Referrer-Policy: strict-origin-when-cross-origin`

## Logging

- Log authentication events (login, logout, failed attempts)
- Log authorization failures
- **Never log** passwords, tokens, API keys, or PII
- Include request IDs for traceability
