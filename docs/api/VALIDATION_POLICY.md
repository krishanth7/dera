# DERA API Validation Policy

This document outlines the validation rules, input constraints, and security bounds enforced across all DERA API endpoints.

---

## 1. Pydantic v2 Validation Architecture

All incoming API requests are validated via Pydantic v2 models inheriting from `DeraBaseModel`:

```python
from dera_api.contracts.base import DeraBaseModel
from pydantic import Field


class CreateCatalogRequest(DeraBaseModel):
    name: str = Field(..., min_length=2, max_length=63, pattern=r"^[a-zA-Z_][a-zA-Z0-9_]*$")
    description: str | None = Field(default=None, max_length=255)
    tags: list[str] = Field(default_factory=list, max_length=10)
```

### Key Principles

1. **Explicit Constraints**: Every string MUST specify `min_length` and `max_length`; every collection MUST specify `max_length`; every integer MUST specify `ge` and `le`.
2. **Deterministic Coercion**: Unambiguous conversions (e.g. string to int in query params) are handled safely; unexpected field additions are handled per-model.
3. **No Unbounded Memory Allocation**: Collections are strictly capped to prevent Denial-of-Service (DoS) attacks via memory exhaustion.

---

## 2. Path & Identifier Validation

Identifier formats are strictly enforced using pre-compiled regular expressions:

| Identifier Type | Regex Constraint | Length Bound | Example |
|---|---|---|---|
| **URL Slug** | `^[a-z0-9]+(?:-[a-z0-9]+)*$` | 1 – 64 characters | `analytics-prod-01` |
| **UUID v4** | `^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5]...` | 36 characters | `a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11` |
| **Database Identifier** | `^[a-zA-Z_][a-zA-Z0-9_]{0,62}$` | 1 – 63 characters | `customer_orders` |
| **Qualified Identifier** | `^[a-zA-Z_]...(?:\.[a-zA-Z_]...)?$` | 1 – 128 characters | `public.customer_orders` |

---

## 3. Security-Sensitive Input Controls

### SQL Injection Prevention

* Raw SQL queries from client input are strictly forbidden.
* Sorting fields and filter condition attributes are validated against `^[a-zA-Z_][a-zA-Z0-9_]{0,63}$` to ensure only legitimate identifier names can be passed.
* Semicolons (`;`), dashes (`--`), comments (`/* */`), quotes (`'`), and SQL keywords are rejected at the contract boundary before execution.

### Path Traversal Defense

* URL slugs and resource names reject directory traversal patterns such as `../`, `..\`, and null bytes (`\0`).

### Request Size & Complexity Bounds

* Query string filters: Maximum 20 filter conditions per request.
* Pagination size: Maximum 100 records per page.
* Collection payload length: Maximum 1,000 items per bulk operation.
