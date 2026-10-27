# Worker Operations & Concurrency

## Celery Configuration

DERA workers operate under hardened constraints in `apps/api/src/dera_api/workers/celery_app.py`:
- `task_serializer = "json"`: JSON-only message bodies.
- `result_serializer = "json"`: Strict JSON results.
- `accept_content = ["json"]`: Rejects any non-JSON payloads (blocks pickle exploits).
- `task_acks_late = True`: Tasks are acknowledged only AFTER execution completes. If a worker process terminates abruptly, the message remains on Redis and is picked up by another worker.
- `worker_prefetch_multiplier = 1`: Disables bulk prefetching to ensure fair queue distribution across workers.
- `task_ignore_result = True`: Celery's transient backend is not the source of truth; results are persisted atomically into PostgreSQL `dera_jobs`.

## Running Workers

```bash
# Start a Celery worker pool
celery -A dera_api.workers.celery_app worker --loglevel=INFO -Q dera_jobs -c 4
```
