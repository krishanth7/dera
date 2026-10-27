"""DERA Workers — Celery Application Configuration.

Configures the background Celery instance for DERA Phase 4.5.
Enforces strict JSON-only serialization, task acknowledgments after execution (acks_late),
single prefetch concurrency for fair scheduling, and zero pickle deserialization.
"""

from celery import Celery

from dera_api.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "dera_worker",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    broker_connection_retry_on_startup=True,
    task_default_queue="dera_jobs",
    task_routes={
        "dera_api.workers.tasks.*": {"queue": "dera_jobs"},
    },
)
