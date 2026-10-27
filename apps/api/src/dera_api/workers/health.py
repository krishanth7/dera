"""DERA Workers — Operational Health and Queue Inspection.

Provides safe internal diagnostics for queue broker connectivity and worker readiness.
"""

from typing import Any
import redis

from dera_api.core.config import get_settings
from dera_api.jobs.registry import default_task_registry
from dera_api.workers.celery_app import celery_app


def check_broker_health() -> dict[str, Any]:
    """Test broker connectivity and inspect ping latency."""
    settings = get_settings()
    try:
        r = redis.Redis.from_url(settings.redis_url, socket_connect_timeout=2.0)
        pong = r.ping()
        return {
            "status": "healthy" if pong else "unhealthy",
            "broker": "redis",
            "connected": bool(pong),
        }
    except Exception as exc:
        return {
            "status": "unhealthy",
            "broker": "redis",
            "connected": False,
            "error": str(exc),
        }


def get_worker_status() -> dict[str, Any]:
    """Inspect local worker configuration and registered tasks."""
    return {
        "status": "ready",
        "registered_tasks": default_task_registry.list_task_types(),
        "task_count": len(default_task_registry.list_task_types()),
        "default_queue": celery_app.conf.task_default_queue,
    }
