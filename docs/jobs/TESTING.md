# Testing & Verification Guide

## Test Suite Inventory

DERA Phase 4.5 includes exhaustive test suites covering:
1. `tests/jobs/test_state_machine.py`: Legal state transitions, rejection of invalid transitions, terminal immutability.
2. `tests/jobs/test_retry_backoff.py`: Backoff calculation, exponential progression, jitter variance, error classification.
3. `tests/jobs/test_task_registry.py`: Statically registered tasks, allowlist rejection of unknown task types.
4. `tests/jobs/test_job_service.py`: Submission, outbox event generation, idempotency deduplication.
5. `tests/workers/test_worker_execution.py`: Atomic CAS claiming, task execution, timeout handling, retry incrementing.
6. `tests/jobs/test_job_endpoints.py`: REST API routing, RBAC role permission checks (`job:create`, `job:read`, `job:cancel`).
7. `tests/tenancy/test_job_tenancy.py`: Multi-tenant isolation between workspaces.
8. `tests/reliability/test_crash_recovery.py`: Broker failure resilience and CAS race conditions.

## Execution

```bash
python scripts/ci/test_reporter.py --test-dir tests/jobs tests/workers tests/tenancy tests/reliability
```
