# Phase 10.1 API Contract

`POST /api/v1/sql-engineering/analyze?workspace_id=<UUID>`

Requires a valid platform session and active workspace membership with `schema:read`.
Cookie sessions require the existing CSRF cookie/header pair. Bearer sessions use the
existing authentication dependency. Client identities and roles are forbidden body fields.

```json
{"sql":"SELECT a.id FROM accounts a WHERE a.id=:id","dialect":"postgresql"}
```

The response is the versioned Analysis model in the generated OpenAPI snapshot at
[openapi.v1.json](../api/openapi.v1.json). It contains dialect, engine_version,
statement_count, statements, diagnostics, unsupported_constructs and aggregate safety.
Each statement contains statement_type, objects, columns, joins, predicates, parameters and safety.
Analysis has no connection identifier and cannot execute or persist submitted SQL.

| Condition | Response |
| --- | --- |
| Completed analysis, including malformed SQL | 200, typed result with diagnostics |
| Missing or invalid session | 401 |
| Missing, inactive or inaccessible workspace, insufficient permission | 403 |
| Missing or invalid workspace UUID, invalid dialect/body, oversized SQL field | 422 |
| Streamed JSON body exceeds 65,536 bytes | 413 |
| Platform database unavailable | Existing platform dependency error handling; access never granted |

The SQL field accepts at most 16,384 characters; the analyzer additionally caps UTF-8 bytes
at 16,384. The raw JSON body cap applies before JSON decoding, regardless of Content-Length.
Byte-limited analysis yields unknown with resource_limit; field validation yields 422.
SQL text is sensitive: result clauses can contain literals, so clients must protect results.
