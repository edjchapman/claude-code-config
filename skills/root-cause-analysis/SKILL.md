---
name: root-cause-analysis
description: Use when investigating incidents, production failures, recurring bugs, regressions, flaky tests, logs, stack traces, or system behavior that needs root-cause analysis.
---

# Root Cause Analysis

When fixing bugs or errors, always distinguish between symptoms and root causes.

## Symptoms vs. Root Causes

**Symptom:** The observed failure or error message.
**Root Cause:** The underlying issue that produced the symptom.

| Symptom                       | Root Cause                        |
| ----------------------------- | --------------------------------- |
| NaN in serialized output      | Division by zero in calculation   |
| 500 error on API endpoint     | Missing validation at entry point |
| Stale data in UI              | Cache invalidation logic missing  |
| Type error in function result | Type mismatch at data source      |

## Investigation Checklist

1. **Ask "Why?" repeatedly** — don't stop at the first answer
2. **Find the earliest point** where the problem originates — don't fix at the display/serialization layer
3. **Check for similar issues** in related code paths
4. **Verify the fix is permanent** — the symptom should disappear naturally from fixing the root cause

## Django Example

Bad — treating the symptom in the serializer:

```python
# serializer.py
def to_representation(self, obj):
    rate = obj.revenue / obj.transactions if obj.transactions else 0
    return {"rate": rate}
```

Good — treating the root cause at the model/calculation layer:

```python
# models.py
@property
def transaction_rate(self):
    if self.transactions == 0:
        return Decimal("0.00")
    return self.revenue / self.transactions

# serializer.py — no special handling needed
def to_representation(self, obj):
    return {"rate": obj.transaction_rate}
```
