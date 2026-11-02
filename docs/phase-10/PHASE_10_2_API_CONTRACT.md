# Phase 10.2 Diagnostics API Contract

`POST /api/v1/sql-engineering/diagnostics?workspace_id=<UUID>`

Uses Phase 10.1's bounded route and strict request model. Canonical dialect values are
`postgresql`, `sqlite`, `mysql`, `mariadb`; the illustrative `postgres` alias is deliberately
not added to the existing contract. Authentication uses existing platform sessions and
schema:read workspace authorization. Snapshot requests additionally require snapshot:read.
Cookie requests use existing CSRF verification.

```json
{
  "sql": "SELECT * FROM accounts",
  "dialect": "postgresql",
  "schema_snapshot_id": null,
  "options": {
    "include_complexity": true,
    "include_recommendations": true
  }
}
```

The typed SqlDiagnosticsReport response contains analysis_status, dialect, the unchanged
Phase 10.1 analysis, optional complexity, ordered findings/recommendations, per-rule evaluations,
total_findings, rules_version, report_version, snapshot_fingerprint and fingerprint.

- COMPLETE: validated AST and no unsupported or unevaluated rule context.
- PARTIAL: validated AST with unsupported syntax or unavailable schema checks.
- INDETERMINATE: no validated AST; no structural score is fabricated.

An unsafe SQL statement can still receive complete structural analysis; the nested analysis
safety classification is authoritative and is never upgraded by diagnostics. Missing schema
means schema rules are NOT_EVALUATED with reasons; most SQL-only requests are therefore PARTIAL.
Aggregate rule locations are null when exact spans cannot be established. Baseline limitation
findings use documented whole-input Unicode spans, with end-exclusive code-point offsets.

| Condition | Response |
| --- | --- |
| Authorized analysis, including malformed or unsupported SQL | 200, typed diagnostic report |
| Missing/forged/expired/revoked session | 401 |
| Unauthorized/inactive workspace or insufficient permission; cookie CSRF failure | 403 |
| Snapshot missing or belonging to another workspace | 404, indistinguishable absence |
| Invalid body/dialect/UUID, incompatible/corrupt/oversized snapshot, oversized SQL field | 422, sanitized error |
| Raw JSON exceeds 65,536 bytes | 413 |

Unknown request properties, including role and user identities, are rejected. Snapshot ID is
at most 200 characters and is only a lookup key; it never grants access. No SQL text or report
is logged or cached by the service. Returned nested analysis metadata may contain SQL literals
and must be treated as sensitive by callers.

See the generated [OpenAPI contract](../api/openapi.v1.json) for exact field schemas and defaults.
