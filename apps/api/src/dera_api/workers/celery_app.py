"""DERA Workers — Celery Application Configuration.

Configures the background Celery instance for DERA Phase 4.5.
Enforces strict JSON-only serialization, task acknowledgments after execution (acks_late),
single prefetch concurrency for fair scheduling, and zero pickle deserialization.
"""

import os
import sys

from celery import Celery

from dera_api.core.config import get_settings

settings = get_settings()

is_testing = (
    settings.environment == "testing"
    or os.getenv("APP_ENV") == "testing"
    or os.getenv("DERA_ENV") == "testing"
    or "pytest" in sys.modules
    or any("test" in arg.lower() for arg in sys.argv)
)

if is_testing:
    broker_url = "memory://"
    result_backend = "cache+memory://"
else:
    broker_url = settings.celery_broker_url
    result_backend = settings.celery_result_backend

celery_app = Celery(
    "dera_worker",
    broker=broker_url,
    backend=result_backend,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    task_ignore_result=True,
    task_store_errors_even_if_ignored=False,
    worker_prefetch_multiplier=1,
    broker_connection_retry_on_startup=False,
    broker_connection_max_retries=0,
    broker_transport_options={
        "max_retries": 0,
        "interval_start": 0,
        "interval_step": 0,
        "interval_max": 0,
    },
    result_backend_transport_options={
        "max_retries": 0,
        "interval_start": 0,
        "interval_step": 0,
        "interval_max": 0,
    },
    task_default_queue="dera_jobs",
    task_routes={
        "dera_api.workers.tasks.*": {"queue": "dera_jobs"},
    },
)

if is_testing:
    celery_app.conf.update(
        broker_url="memory://",
        result_backend="cache+memory://",
    )
