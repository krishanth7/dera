"""DERA Database — Session Factory & Transaction Management.

Provides async session creation and explicit transaction context managers
ensuring predictable transaction boundaries, deterministic commits, and
guaranteed rollbacks on failure without connection leaks.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Create a configured async sessionmaker bound to the given engine.

    Parameters
    ----------
    engine : AsyncEngine
        SQLAlchemy AsyncEngine to bind sessions to.

    Returns
    -------
    async_sessionmaker[AsyncSession]
        Configured session factory.
    """
    return async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )


@asynccontextmanager
async def transaction_scope(session: AsyncSession) -> AsyncIterator[AsyncSession]:
    """Provide an explicit transaction boundary around a block of operations.

    Commits atomically upon successful completion of the block.
    Automatically rolls back on any exception and re-raises the error.

    Parameters
    ----------
    session : AsyncSession
        Active database session to manage the transaction on.

    Yields
    ------
    AsyncSession
        The session with an active transaction.
    """
    is_outer = not session.info.get("_dera_tx_active", False)
    if is_outer:
        session.info["_dera_tx_active"] = True
        try:
            if not session.in_transaction():
                async with session.begin():
                    yield session
            else:
                try:
                    yield session
                    await session.commit()
                except Exception:
                    await session.rollback()
                    raise
        finally:
            session.info["_dera_tx_active"] = False
    else:
        # Nested transaction scope establishes a savepoint
        async with session.begin_nested():
            yield session


@asynccontextmanager
async def session_scope(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncSession]:
    """Provide an isolated, managed AsyncSession scope with guaranteed closure.

    Parameters
    ----------
    session_factory : async_sessionmaker[AsyncSession]
        Session maker used to instantiate the session.

    Yields
    ------
    AsyncSession
        Acquired session instance.
    """
    async with session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
