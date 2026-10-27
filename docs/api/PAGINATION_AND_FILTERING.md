# DERA Pagination & Filtering Standards

This specification outlines the reusable contracts for pagination, sorting, and filtering across all DERA collection endpoints.

---

## 1. Pagination Contract

DERA supports two complementary pagination mechanisms:

1. **Offset Pagination**: For user interfaces and bounded collections requiring random access to page numbers.
2. **Cursor Pagination**: For large, continuous, or streaming datasets where stable ordering without duplicate or missing rows is critical.

### Query Parameters: `PaginationParams`

| Parameter | Type | Default | Constraints | Description |
|---|---|---|---|---|
| `page` | integer | `1` | `>= 1` | 1-based page index for offset pagination |
| `page_size` | integer | `50` | `1 <= page_size <= 100` | Number of items requested per page |
| `cursor` | string | `null` | Optional opaque string | Cursor token for deterministic traversal |

### Response Model: `PaginatedResponse[T]`

```json
{
  "items": [
    { "id": "sch_01", "name": "public" },
    { "id": "sch_02", "name": "inventory" }
  ],
  "pagination": {
    "page": 1,
    "page_size": 50,
    "total_items": 124,
    "total_pages": 3,
    "has_next": true,
    "has_previous": false,
    "next_cursor": "ZXhhbXBsZS1jdXJzb3ItdG9rZW4="
  },
  "meta": {
    "request_id": "req-9c8b7a6d",
    "timestamp": "2026-10-27T12:00:00Z",
    "version": "0.1.0-dev"
  }
}
```

---

## 2. Sorting Contract: `SortParams`

Sorting parameters require explicit allowlisting to prevent non-deterministic order or SQL injection.

### Sorting Fields

* `sort_by` (or `field`): Target attribute name validated against `^[a-zA-Z_][a-zA-Z0-9_]{0,63}$`.
* `order`: Direction enum:
  * `asc`: Ascending order (default).
  * `desc`: Descending order.

Example URL:

```http
GET /api/v1/schemas?sort_by=created_at&order=desc
```

---

## 3. Filtering Contract: `FilterParams`

DERA enforces typed, allowlist-only filter expressions. Arbitrary SQL WHERE clauses are strictly prohibited.

### Allowlisted Filter Operators (`FilterOperator`)

| Operator | Symbol | Meaning | Example Payload |
|---|---|---|---|
| `eq` | `=` | Equal to | `{"field": "status", "operator": "eq", "value": "active"}` |
| `neq` | `!=` | Not equal to | `{"field": "status", "operator": "neq", "value": "archived"}` |
| `gt` | `>` | Greater than | `{"field": "table_count", "operator": "gt", "value": 10}` |
| `gte` | `>=` | Greater than or equal to | `{"field": "table_count", "operator": "gte", "value": 10}` |
| `lt` | `<` | Less than | `{"field": "column_count", "operator": "lt", "value": 50}` |
| `lte` | `<=` | Less than or equal to | `{"field": "column_count", "operator": "lte", "value": 50}` |
| `in` | `IN` | Contained in set | `{"field": "type", "operator": "in", "value": ["BASE TABLE", "VIEW"]}` |
| `like` | `LIKE` | Case-sensitive pattern match | `{"field": "name", "operator": "like", "value": "audit_%"}` |
| `ilike` | `ILIKE` | Case-insensitive pattern match | `{"field": "name", "operator": "ilike", "value": "%user%"}` |
| `is_null` | `IS NULL` | Field value is null | `{"field": "deleted_at", "operator": "is_null", "value": true}` |
| `is_not_null` | `IS NOT NULL` | Field value is not null | `{"field": "updated_at", "operator": "is_not_null", "value": true}` |

### Complexity Boundary

A single request may contain at most **20 filter conditions** (`max_length=20` on `FilterParams`). Requests exceeding this limit receive `422 Unprocessable Entity` with `VALUE_TOO_LARGE`.
