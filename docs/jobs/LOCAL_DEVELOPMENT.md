# Local Development Guide

## Prerequisites

- Python 3.12+
- Redis (optional for local testing; memory broker is used in tests)
- PostgreSQL or SQLite (aiosqlite)

## Environment Variables

Configure in `.env`:
```ini
DERA_CELERY_BROKER_URL=redis://localhost:6379/0
DERA_CELERY_RESULT_BACKEND=redis://localhost:6379/1
DERA_JOB_DEFAULT_TIMEOUT_SECONDS=300
```

## Running Unit & Integration Tests

```bash
python scripts/ci/test_reporter.py --test-dir tests/jobs
python scripts/ci/test_reporter.py --test-dir tests/workers
```
