# Idempotency & Deduplication

## Scoped Idempotency Keys

Clients submitting asynchronous jobs can provide an `idempotency_key` in the request header or body.

### Semantics
1. **Workspace Scope:** Idempotency keys are strictly scoped to the workspace (`workspace_id, idempotency_key`). Two different workspaces may reuse the same idempotency key string without cross-tenant conflict.
2. **Deduplication:** When an identical request is submitted with an existing key, DERA returns the existing `JobResponse` with HTTP 201 Created and identical identifiers.
3. **Conflict Detection:** If a request provides an existing idempotency key but differing job parameters (`job_type` or `payload`), DERA rejects the request with HTTP 409 Conflict (`IDEMPOTENCY_CONFLICT`).
