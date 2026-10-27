"""DERA API — Modern Application Lifespan Management.

Manages application initialization, state readiness, and graceful shutdown
using contextlib.asynccontextmanager without deprecated startup/shutdown events.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Any

from dera_api.core.config import get_settings
from dera_api.core.logging import get_logger
from fastapi import FastAPI

logger = get_logger("dera_api.lifespan")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manages application startup and graceful shutdown sequences."""
    settings = getattr(app.state, "settings", None) or get_settings()

    # Startup sequence
    startup_time = datetime.now(UTC)
    app.state.startup_time = startup_time
    app.state.is_ready = True
    app.state.service_name = "dera-api"
    app.state.version = settings.version

    logger.info(
        "Application startup complete: %s v%s [env=%s, docs=%s]",
        settings.app_name,
        settings.version,
        settings.environment,
        settings.docs_enabled,
    )

    try:
        yield
    finally:
        # Graceful shutdown sequence
        app.state.is_ready = False
        logger.info("Application shutdown initiated; cleaning up resources.")
        logger.info("Application shutdown complete.")


def get_application_readiness(app: FastAPI) -> dict[str, Any]:
    """Returns truthful readiness status and system probe states."""
    is_ready = getattr(app.state, "is_ready", False)
    startup_time = getattr(app.state, "startup_time", None)

    return {
        "ready": bool(is_ready),
        "startup_time": startup_time.isoformat() if startup_time else None,
        "subsystems": {
            "application_state": "operational" if is_ready else "not_ready",
            "database_connectors": "none_required_in_phase_4_1",
            "background_workers": "none_required_in_phase_4_1",
        },
    }
