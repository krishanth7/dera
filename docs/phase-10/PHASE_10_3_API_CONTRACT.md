# Phase 10.3 Imported Plan API

`POST /api/v1/sql-engineering/execution-plans/analyze?workspace_id=<UUID>`

Requires an active authenticated session, active workspace membership and `schema:read`.
Cookie requests require the existing CSRF cookie/header pair. Bearer identities are resolved by
the server. No user ID, role, database ID or connection ID is accepted in the body.

```json
{
  "dialect": "postgresql",
  "format": "postgresql-json",
  "plan_json": "{\"Plan\":{\"Node Type\":\"Seq Scan\",\"Plan Rows\":10000,\"Total Cost\":250}}",
  "sql": null
}
```

The brief's illustrative nested `plan` field is deliberately replaced by `plan_json`: a string
allows raw imported JSON nesting to be checked before the standard decoder is invoked. The
format token explicitly selects the dialect format. No automatic format/dialect reinterpretation.

Successful 200 responses use ExecutionPlan in [OpenAPI](../api/openapi.v1.json), including
nullable metrics, flat nodes and parent/child IDs, summary, findings/recommendations, imported
provenance, canonical native metadata, optional Phase 10.2 SQL report and report fingerprint.
Status COMPLETE means recognized structure, not complete metric coverage or an optimal plan;
PARTIAL identifies unsupported operations. Success carries `Cache-Control: no-store`.

| Status | Meaning |
|---|---|
| 401 | Anonymous, invalid, expired or revoked session |
| 403 | CSRF, inactive/foreign workspace, membership or permission denial |
| 413 | Raw streamed body exceeds 1,200,000 bytes |
| 422 | Invalid request, format mismatch, malformed, invalid numeric, reference or over-limit import |

Imported plan text: 1,048,576 UTF-8 bytes and characters; individual decoded strings 16,384 bytes;
labels 2,048 characters; raw JSON container depth 64; total decoded values/keys 50,000;
normalized nodes 1,000; normalized depth 48. Both depth limits apply, so nested PostgreSQL Plans
arrays can hit the raw limit before normalized depth 48. Known numeric metrics must be finite,
nonnegative and at most 10^15. Optional SQL retains Phase 10.1's independent parsing limits.

Errors follow existing Problem Details conventions and exclude plan/SQL values. No import is
persisted, fetched from a URL or acquired from a customer database. Associated SQL is supplied
by the caller and its correspondence with the plan is explicitly unverified.

The outer request envelope also receives a raw depth-64 scan before FastAPI decoding, so a
malicious nested value cannot bypass the imported-string guard by using an invalid field type.
