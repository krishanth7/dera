"""DERA Database — Asynchronous Engine Factory & Connection Lifecycle.

Manages the creation, configuration, connection pooling, and disposal of the
SQLAlchemy 2.x AsyncEngine for DERA's authoritative platform database.
"""

from typing import Any

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.pool import AsyncAdaptedQueuePool, NullPool, StaticPool

from dera_api.core.config import ApiSettings


def create_database_engine(
    settings: ApiSettings,
    *,
    poolclass: type | None = None,
    **engine_kwargs: Any,
) -> AsyncEngine:
    """Create a configured SQLAlchemy 2.x AsyncEngine.

    Parameters
    ----------
    settings : ApiSettings
        Application configuration containing validated database and pool settings.
    poolclass : type, optional
        Explicit pool class override (e.g., StaticPool or NullPool for testing).
    **engine_kwargs : Any
        Additional keyword arguments forwarded to create_async_engine.

    Returns
    -------
    AsyncEngine
        Configured SQLAlchemy asynchronous engine.

    Raises
    ------
    ValueError
        If no platform database URL is configured in settings.
    """
    if not settings.has_database_configured:
        raise ValueError(
            "Platform database URL is not configured. "
            "Set DERA_PLATFORM_DATABASE_URL or specify database_url in settings."
        )

    db_url = settings.database_url
    connect_args: dict[str, Any] = {}

    if db_url.startswith("sqlite"):
        # SQLite async dialect configuration (used for ephemeral testing)
        chosen_pool = poolclass or (StaticPool if ":memory:" in db_url else NullPool)
        connect_args["check_same_thread"] = False
        return create_async_engine(
            db_url,
            poolclass=chosen_pool,
            connect_args=connect_args,
            echo=settings.db_echo,
            **engine_kwargs,
        )

    # PostgreSQL dialect configuration
    if "asyncpg" in db_url:
        connect_args["timeout"] = settings.db_connect_timeout
        connect_args["command_timeout"] = float(settings.db_statement_timeout_ms) / 1000.0
        connect_args["server_settings"] = {
            "statement_timeout": str(settings.db_statement_timeout_ms),
        }
        if settings.db_ssl_mode != "disable":
            connect_args["ssl"] = settings.db_ssl_mode

    chosen_pool = poolclass or AsyncAdaptedQueuePool

    if chosen_pool is AsyncAdaptedQueuePool:
        return create_async_engine(
            db_url,
            poolclass=chosen_pool,
            pool_size=settings.db_pool_size,
            max_overflow=settings.db_max_overflow,
            pool_timeout=settings.db_pool_timeout,
            pool_recycle=settings.db_pool_recycle,
            pool_pre_ping=True,
            connect_args=connect_args,
            echo=settings.db_echo,
            **engine_kwargs,
        )

    return create_async_engine(
        db_url,
        poolclass=chosen_pool,
        pool_pre_ping=True,
        connect_args=connect_args,
        echo=settings.db_echo,
        **engine_kwargs,
    )


async def dispose_database_engine(engine: AsyncEngine | None) -> None:
    """Safely dispose of the database engine and release all pooled connections.

    Parameters
    ----------
    engine : AsyncEngine | None
        The engine instance to dispose. If None, operation is a safe no-op.
    """
    if engine is not None:
        await engine.dispose()
