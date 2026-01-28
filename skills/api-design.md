---
name: api-design
description: REST conventions, status codes, pagination, and error format standards for API development.
globs:
  - "**/views/**"
  - "**/api/**"
  - "**/serializers/**"
  - "**/routes/**"
  - "**/controllers/**"
  - "**/endpoints/**"
  - "**/schemas/**"
---

# API Design Standards

Apply these conventions when building or reviewing REST APIs.

## URL Structure

- Use nouns, not verbs: `/users` not `/getUsers`
- Plural resource names: `/users`, `/orders`, `/products`
- Nested resources for clear ownership: `/users/{id}/orders`
- Maximum 2 levels of nesting; beyond that, use query parameters
- Use kebab-case: `/user-profiles` not `/userProfiles`

## HTTP Methods

| Method | Purpose | Idempotent | Response |
|--------|---------|------------|----------|
| GET | Read resource(s) | Yes | 200 with data |
| POST | Create resource | No | 201 with created resource |
| PUT | Full replace | Yes | 200 with updated resource |
| PATCH | Partial update | Yes | 200 with updated resource |
| DELETE | Remove resource | Yes | 204 no content |

## Status Codes

Use the correct status code for the situation:

### Success
- `200 OK` -- successful GET, PUT, PATCH
- `201 Created` -- successful POST that creates a resource
- `204 No Content` -- successful DELETE

### Client Errors
- `400 Bad Request` -- validation failure, malformed input
- `401 Unauthorized` -- missing or invalid authentication
- `403 Forbidden` -- authenticated but lacking permission
- `404 Not Found` -- resource doesn't exist
- `409 Conflict` -- duplicate resource, state conflict
- `422 Unprocessable Entity` -- valid syntax but semantic errors
- `429 Too Many Requests` -- rate limit exceeded

### Server Errors
- `500 Internal Server Error` -- unexpected server failure
- `503 Service Unavailable` -- temporary overload or maintenance

## Error Response Format

Use a consistent error structure across all endpoints:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "The request contains invalid fields.",
    "details": [
      {
        "field": "email",
        "message": "Must be a valid email address."
      }
    ]
  }
}
```

- Always include a machine-readable `code`
- Include human-readable `message`
- Use `details` array for field-level validation errors
- Never expose stack traces or internal details in production

## Pagination

Use cursor-based or offset-based pagination for list endpoints:

```json
{
  "data": [...],
  "pagination": {
    "next_cursor": "abc123",
    "has_more": true,
    "total_count": 142
  }
}
```

- Default page size: 20, max: 100
- Include `total_count` when practical (skip for expensive counts)
- Use `cursor` param for cursor-based, `page`/`limit` for offset-based

## Filtering and Sorting

- Filter with query params: `GET /users?status=active&role=admin`
- Sort with `sort` param: `GET /users?sort=-created_at` (prefix `-` for descending)
- Search with `q` or `search` param: `GET /users?q=john`

## Versioning

- Use URL path versioning: `/api/v1/users`
- Only increment major version for breaking changes
- Support previous version for a documented deprecation period

## Response Envelope

Wrap responses consistently:

```json
{
  "data": { ... },
  "meta": {
    "request_id": "req_abc123",
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

## Rate Limiting

- Return `429 Too Many Requests` when limit exceeded
- Include headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`
- Apply per-user or per-API-key, not per-IP alone
