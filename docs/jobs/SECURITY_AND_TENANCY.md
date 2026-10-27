# Security & Tenant Isolation

## Multi-Tenant Isolation

1. **Workspace Boundary:** Every job is permanently bound to `workspace_id`.
2. **Access Control:** All endpoints require authenticated Bearer sessions and explicit permissions:
   - `job:create` to submit jobs.
   - `job:read` to inspect job status and list jobs.
   - `job:cancel` to request cancellation.
3. **Cross-Tenant Prevention:** Attempting to read or cancel a job belonging to Workspace A with a token for Workspace B returns HTTP 404 Not Found (`JOB_NOT_FOUND`), preventing tenant resource enumeration.

## Credential Safety

No credentials or authentication tokens are ever stored in job payloads or outbox event tables. Tasks needing credentials must resolve them via internal server-side vaults scoped to the workspace.
