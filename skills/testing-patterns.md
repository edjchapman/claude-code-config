---
name: testing-patterns
description: Enforces AAA pattern, factory usage, and coverage expectations for Python and TypeScript tests.
globs:
  - "**/test_*.py"
  - "**/*_test.py"
  - "**/tests/**/*.py"
  - "**/*.test.ts"
  - "**/*.test.tsx"
  - "**/*.spec.ts"
  - "**/*.spec.tsx"
  - "**/tests/**/*.ts"
---

# Testing Patterns

Apply these patterns when writing or reviewing tests.

## Structure: Arrange-Act-Assert (AAA)

Every test should follow the AAA pattern with clear visual separation:

```python
def test_user_creation_with_valid_data():
    # Arrange
    user_data = {"email": "test@example.com", "name": "Test User"}

    # Act
    user = UserService.create(user_data)

    # Assert
    assert user.email == "test@example.com"
    assert user.is_active is True
```

```typescript
it("creates a user with valid data", () => {
  // Arrange
  const userData = { email: "test@example.com", name: "Test User" };

  // Act
  const user = UserService.create(userData);

  // Assert
  expect(user.email).toBe("test@example.com");
  expect(user.isActive).toBe(true);
});
```

## Naming Convention

Test names should describe the scenario and expected outcome:

- Python: `test_<unit>_<scenario>_<expected_result>`
- TypeScript: `"<unit> <scenario> <expected result>"`

Good: `test_login_with_invalid_password_returns_401`
Bad: `test_login`, `test_case_1`

## Test Data

### Use Factories (not fixtures for mutable data)

- Python: `factory_boy` or custom factory functions
- TypeScript: builder pattern or factory functions
- Never hardcode IDs or timestamps -- use factories to generate them
- Share setup via factory defaults, override per-test as needed

### Isolation

- Each test must be independent -- no shared mutable state
- Use fresh database transactions per test (Django: `TestCase` or `@pytest.mark.django_db`)
- Mock external services at the boundary (HTTP, email, queues)

## What to Test

### Must Test

- Happy path for every public function/endpoint
- Error/edge cases: null inputs, empty collections, boundary values
- Authorization: ensure protected routes reject unauthorized access
- Validation: verify invalid input is rejected with correct errors

### Don't Test

- Private/internal methods directly (test through public interface)
- Framework code (Django ORM, React rendering engine)
- Trivial getters/setters with no logic

## Coverage Expectations

- New code: aim for 80%+ line coverage
- Critical paths (auth, payments, data mutations): 95%+
- Don't chase 100% -- focus on meaningful assertions over line coverage

## Mocking Guidelines

- Mock at boundaries: HTTP clients, databases, file systems, clocks
- Prefer dependency injection over patching
- Verify mock interactions only when the side effect IS the behavior
- Don't mock the thing you're testing
