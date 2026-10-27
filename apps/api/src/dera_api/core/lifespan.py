"""DERA API — Modern Application Lifespan Management.

Manages application initialization, state readiness, and graceful shutdown
using contextlib.asynccontextmanager without deprecated startup/shutdown events.
Integrates platform database engine lifecycle, pooling, and disposal.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Any

from dera_api.core.config import get_settings
from dera_api.core.logging import get_logger
from dera_api.db.engine import create_database_engine, dispose_database_engine
from dera_api.db.session import create_session_factory
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

    # Platform database initialization
    if settings.has_database_configured:
        try:
            engine = create_database_engine(settings)
            session_factory = create_session_factory(engine)
            app.state.db_engine = engine
            app.state.db_session_factory = session_factory
            logger.info(
                "Platform database engine initialized: [url=%s, pool_size=%d, max_overflow=%d]",
                settings.sanitized_database_url,
                settings.db_pool_size,
                settings.db_max_overflow,
            )
        except Exception as exc:
            logger.error("Failed to initialize platform database engine: %s", exc)
            app.state.db_engine = None
            app.state.db_session_factory = None
            app.state.is_ready = False
            raise
    else:
        app.state.db_engine = None
        app.state.db_session_factory = None
        logger.info("Platform database not configured; operating in stateless mode.")

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

        db_engine = getattr(app.state, "db_engine", None)
        if db_engine is not None:
            await dispose_database_engine(db_engine)
            logger.info("Platform database engine cleanly disposed.")

        logger.info("Application shutdown complete.")


def get_application_readiness(app: FastAPI) -> dict[str, Any]:
    """Returns truthful readiness status and system probe states."""
    is_ready = getattr(app.state, "is_ready", False)
    startup_time = getattr(app.state, "startup_time", None)
    db_engine = getattr(app.state, "db_engine", None)

    db_status = "operational" if db_engine is not None else "not_configured"

    return {
        "ready": bool(is_ready),
        "startup_time": startup_time.isoformat() if startup_time else None,
        "subsystems": {
            "application_state": "operational" if is_ready else "not_ready",
            "database_connectors": "none_required_in_phase_4_1",
            "background_workers": "none_required_in_phase_4_1",
            "platform_database": db_status,
        },
    }
