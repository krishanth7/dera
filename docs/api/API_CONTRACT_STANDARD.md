# DERA Canonical API Contract Standard

This standard dictates conventions for path naming, serialization, data types, and status code semantics across all DERA REST endpoints.

---

## 1. URI & Path Conventions

1. **Prefix**: All v1 REST endpoints MUST begin with `/api/v1/`.
2. **Resource Naming**: Plural nouns in kebab-case (e.g. `/api/v1/database-connections`, `/api/v1/catalogs`).
3. **Sub-resources**: Hierarchy follows ownership (e.g. `/api/v1/catalogs/{catalog_id}/schemas`).
4. **Action Endpoints**: Prefer standard HTTP verbs over RPC actions. If a non-CRUD operation is required, use lowercase verbs as sub-paths (e.g. `/api/v1/reports/{id}/export`).

---

## 2. JSON Field Naming & Serialization

1. **Casing**: All JSON keys MUST use `snake_case` (e.g. `request_id`, `total_items`, `created_at`).
2. **Encoding**: Responses MUST be UTF-8 encoded with `Content-Type: application/json; charset=utf-8` or `application/problem+json; charset=utf-8`.
3. **Null Handling**: Fields MUST be explicitly `null` when a value is nullable; omitted fields are reserved for optional request payloads only.
4. **Non-Finite Floats**: Standard JSON forbids `NaN`, `Infinity`, and `-Infinity`. Any numeric calculations yielding undefined values MUST serialize as `null` or return a domain error.

---

## 3. Data Representation Standards

| Type | Format & Convention | Example |
|---|---|---|
| **Timestamps** | ISO 8601 UTC with explicit `Z` suffix | `"2026-10-27T12:00:00Z"` |
| **Dates** | ISO 8601 calendar date | `"2026-10-27"` |
| **UUIDs** | Lowercase canonical hyphenated 36-character string | `"a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"` |
| **Decimals** | String or bounded numeric to prevent precision loss | `"1299.95"` or `1299.95` |
| **Enums** | Uppercase or lowercase string values (consistent per contract) | `"active"`, `"VALIDATION_ERROR"` |
| **Identifiers** | Safe database or URL slugs (bounded by regex) | `"users_table"`, `"public-schema"` |

---

## 4. HTTP Verb & Status Code Semantics

DERA adheres strictly to RFC 9110 HTTP semantics:

| HTTP Verb | Safe | Idempotent | Success Status Codes |
|---|---|---|---|
| **GET** | Yes | Yes | `200 OK` |
| **HEAD** | Yes | Yes | `200 OK` (headers only) |
| **POST** | No | No | `201 Created` (with resource), `202 Accepted` (async), `200 OK` |
| **PUT** | No | Yes | `200 OK`, `204 No Content` |
| **PATCH** | No | No | `200 OK` |
| **DELETE** | No | Yes | `200 OK`, `204 No Content` |

### Error Status Codes

* `400 Bad Request`: Malformed syntax, invalid JSON payload structure.
* `404 Not Found`: Target resource does not exist.
* `405 Method Not Allowed`: Unsupported HTTP verb on the targeted route.
* `409 Conflict`: Concurrency conflict, resource state mismatch.
* `415 Unsupported Media Type`: Request payload is not `application/json`.
* `422 Unprocessable Entity`: Request body or parameters failed typed Pydantic validation.
* `429 Too Many Requests`: Client exceeded rate limiting quotas.
* `500 Internal Server Error`: Unhandled server exception (tracebacks scrubbed).
* `503 Service Unavailable`: Target dependency or database engine unresponsive.

---

## 5. Success Envelopes

For endpoints returning operational metadata or tracking correlation, DERA provides standardized envelopes:

### Single Resource: `DataEnvelope[T]`

```json
{
  "data": {
    "id": "cat_01",
    "name": "primary_postgres"
  },
  "meta": {
    "request_id": "req-7f8d6e5a",
    "timestamp": "2026-10-27T12:00:00Z",
    "version": "0.1.0-dev"
  }
}
```

### Unpaginated Collection: `CollectionEnvelope[T]`

```json
{
  "items": [
    { "id": "1", "name": "public" },
    { "id": "2", "name": "analytics" }
  ],
  "total": 2,
  "meta": {
    "request_id": "req-7f8d6e5a",
    "timestamp": "2026-10-27T12:00:00Z",
    "version": "0.1.0-dev"
  }
}
```
