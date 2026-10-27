# Job Lifecycle & State Machine

## State Taxonomy

The DERA Job lifecycle is governed by an explicit finite state machine (`JobStatus`):

| State | Category | Description |
|---|---|---|
| `PENDING` | Active | Job created in PostgreSQL platform database; transactional outbox event written. |
| `QUEUED` | Active | Outbox event dispatched to Celery message queue; awaiting worker claim. |
| `RUNNING` | Active | Atomically claimed by worker; handler actively executing. |
| `SUCCEEDED` | Terminal | Handler executed successfully; typed result dictionary persisted. |
| `FAILED` | Terminal | Execution failed; retries exhausted or non-retryable error encountered. |
| `CANCELLED` | Terminal | Cancellation requested by authorized tenant and acknowledged prior to or during execution. |

## Allowed Transitions

The transition graph is strictly enforced by `validate_transition(current, target)`:

```text
[PENDING] ----> [QUEUED] ----> [RUNNING] ----> [SUCCEEDED]
    |               |               |
    |               |               +--------> [FAILED]
    |               |               |
    +---------------+---------------+--------> [CANCELLED]
```

### Invariants
1. **Terminal Immutability:** Once in `SUCCEEDED`, `FAILED`, or `CANCELLED`, no further transitions are permitted. Any attempt raises `JobAlreadyCompletedError`.
2. **Atomic CAS Claims:** A worker can only transition a job from `QUEUED` to `RUNNING`. Transitioning from `PENDING` directly to `RUNNING` is rejected with `InvalidStateTransitionError`.
