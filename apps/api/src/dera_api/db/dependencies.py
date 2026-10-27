"""DERA Database — FastAPI Dependency Injection.

Provides request-scoped AsyncSession dependency injection with deterministic
transaction cleanup, exception rollback, and guaranteed session disposal.
"""

from collections.abc import AsyncIterator

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from dera_api.core.exceptions import DependencyUnavailableError


async def get_db_session(request: Request) -> AsyncIterator[AsyncSession]:
    """Provide a request-scoped AsyncSession with guaranteed cleanup.

    Parameters
    ----------
    request : Request
        Incoming HTTP request holding application state.

    Yields
    ------
    AsyncSession
        Managed SQLAlchemy asynchronous session.

    Raises
    ------
    DependencyUnavailableError
        If the platform database has not been configured or initialized.
    """
    session_factory: async_sessionmaker[AsyncSession] | None = getattr(
        request.app.state, "db_session_factory", None
    )

    if session_factory is None:
        raise DependencyUnavailableError(
            "Platform database is not configured or currently unavailable."
        )

    async with session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
