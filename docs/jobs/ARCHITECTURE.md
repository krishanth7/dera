# Background Jobs Architecture

## System Topography

The DERA Job Orchestration architecture implements a dual-store model:
1. **Durable Platform Persistence (PostgreSQL):** The authoritative system of record for job definitions, state transitions, execution logs, attempt metrics, and transactional outbox events (`dera_jobs`, `dera_job_outbox`).
2. **Transient Message Broker (Redis / Celery):** High-throughput, distributed dispatch queue used for worker notification and scheduling (`dera_jobs` queue).

```text
+-------------------------------------------------------------+
| FastAPI Gateway (API Layer)                                 |
| POST /api/v1/workspaces/{workspace_id}/jobs                 |
+------------------------------+------------------------------+
                               | (1) Atomic Transaction
                               v
+-------------------------------------------------------------+
| PostgreSQL Platform Persistence                             |
|  - INSERT dera_jobs (status = PENDING)                      |
|  - INSERT dera_job_outbox (status = PENDING)                |
+------------------------------+------------------------------+
                               | (2) Transaction Commit Hook
                               v
+-------------------------------------------------------------+
| JobOutboxDispatcher                                         |
|  - apply_async(job_id, workspace_id) to Celery              |
|  - UPDATE dera_jobs SET status = QUEUED                     |
|  - UPDATE dera_job_outbox SET status = DISPATCHED           |
+------------------------------+------------------------------+
                               | (3) Redis Protocol
                               v
+-------------------------------------------------------------+
| Celery Distributed Worker                                   |
|  - Atomic CAS Claim: UPDATE dera_jobs SET status = RUNNING  |
|  - Load Typed Task from TaskRegistry                        |
|  - Execute Handler with Timeout Wrapper                     |
|  - UPDATE dera_jobs SET status = SUCCEEDED / FAILED         |
+-------------------------------------------------------------+
```

## Resilience Guarantees

- **No Dual-Write Vulnerability:** If the application crashes between inserting the job and sending to Celery, the job is committed to PostgreSQL outbox. The background outbox poller discovers and republishes it.
- **Compare-And-Swap (CAS) Concurrency:** Worker claiming requires `UPDATE dera_jobs SET status = 'running', worker_id = :worker_id WHERE id = :id AND status = 'queued'`. If two workers attempt to claim the same job, exactly one succeeds.
- **Cooperative Cancellation:** Workers check `cancellation_requested` flags during long-running tasks. Terminal jobs cannot be transitioned to running.
