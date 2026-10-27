# Failure Recovery & Outbox Delivery

## Outbox Pattern & Broker Outages

If the Celery / Redis broker is unavailable when a job is created:
1. The database transaction committing the `Job` and `JobOutboxEvent` still succeeds.
2. The synchronous dispatch hook fails gracefully, logging a warning and incrementing `dispatch_attempts`.
3. The outbox record remains in `status = 'pending'`.
4. The background `JobOutboxDispatcher.dispatch_pending_events()` routinely scans for pending outbox entries and publishes them once the broker recovers.

## Worker Crash Recovery

If a worker crashes mid-task:
1. Since `task_acks_late = True`, Redis redelivers the message to a surviving worker.
2. The surviving worker queries `dera_jobs`. If the job was claimed by a dead worker, heartbeat / timeout detection allows reclaiming or re-enqueueing the job.
