# Phase 10.3 Security Boundaries

## Prohibited capabilities

No customer database dependency, connection, EXPLAIN endpoint, ANALYZE invocation, query
execution, SQL rewrite, index creation, external inference or AI dependency exists in this package.
Imported actual metrics may be inspected; they do not authorize collecting them. A future live
acquisition workflow needs separate security design and approval.

## Input and resource controls

The route bounds streamed bytes before FastAPI decoding, including chunked bodies. Imported
JSON is a string with an independent UTF-8 byte bound and a pre-decoder container-depth scan.
Duplicate keys, non-finite values, oversized scalars, invalid numeric types and tree/reference
cycles are rejected. Value count, normalized node count and depth are bounded. No eval, pickle,
YAML, external URI loader or dynamic SQL API is used. These are bounded workloads, not hard
wall-clock/process memory quotas; deployment-level concurrency/rate limits remain operational
controls. Native metadata and filters can be sensitive and must be handled accordingly.

## Authorization and tenant isolation

Existing opaque-session resolution rejects revoked/expired sessions and inactive accounts.
Existing server-authoritative workspace membership and `schema:read` checks are reused without
production overrides. Cookie CSRF remains enforced. Client roles/identities/connections are
forbidden extras. There is no workspace-shared plan cache or persistence. Frontend request
cancellation and workspace-keyed remounts prevent previous-workspace results appearing after a
workspace switch. Analysis responses are no-store and no local-storage plan persistence is added.

## Logging and output

No plan text or associated SQL is logged. Safe parse failures use fixed messages; request
validation uses the existing safe error normalization. Logs contain normal request metadata,
not imported payloads. Native metadata is returned to the authorized caller, clearly labelled and
rendered as escaped React text. No HTML injection renderer is used. Imports remain unverified
claims from the caller, not trusted database provenance or proof of plan-to-SQL correspondence.

Tests cover real sessions, CSRF, foreign workspace access, identity spoofing, rejected connection
IDs, size/depth errors, connector-spy regressions and sensitive-plan logging. See
[test evidence](PHASE_10_3_TEST_REPORT.md).

The outer request envelope also receives a raw depth-64 scan before FastAPI decoding, so a
malicious nested value cannot bypass the imported-string guard by using an invalid field type.
