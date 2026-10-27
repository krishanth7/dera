# Cooperative Job Cancellation

## Cancellation Semantics

Clients with `job:cancel` permission can request cancellation of an active job via:
`POST /api/v1/workspaces/{workspace_id}/jobs/{job_id}/cancel`

### Scenarios:
1. **Pending / Queued Jobs:** If the job has not yet started running, `request_cancellation` marks the job directly as `CANCELLED` and marks pending outbox events as cancelled, preventing execution.
2. **Running Jobs:** If the job is `RUNNING`, `cancellation_requested` is set to `True`. The worker inspects `ctx.is_cancelled` during cooperative yield points and safely terminates execution, updating status to `CANCELLED`.
3. **Terminal Jobs:** If the job is already `SUCCEEDED`, `FAILED`, or `CANCELLED`, the endpoint returns HTTP 409 Conflict (`JOB_ALREADY_COMPLETED`).
