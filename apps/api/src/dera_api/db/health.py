"""DERA Database — Health & Readiness Probe Check.

Provides a lightweight, bounded database connectivity check (SELECT 1;)
for use in readiness probes and operational diagnostic health endpoints.
"""

import asyncio
import logging
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

logger = logging.getLogger("dera_api.db.health")


async def check_database_health(
    engine: AsyncEngine | None,
    timeout_seconds: float = 3.0,
) -> bool:
    """Execute a lightweight bounded query to verify database connectivity.

    Parameters
    ----------
    engine : AsyncEngine | None
        The active database engine to probe.
    timeout_seconds : float
        Maximum duration to wait for the probe to respond before failing.

    Returns
    -------
    bool
        True if the database successfully responded to 'SELECT 1;', False otherwise.
    """
    if engine is None:
        return False

    try:
        async with asyncio.timeout(timeout_seconds):
            async with engine.connect() as conn:
                result = await conn.execute(text("SELECT 1;"))
                scalar_val: Any = result.scalar()
                return scalar_val == 1
    except TimeoutError:
        logger.warning("Database readiness probe timed out after %.2f seconds", timeout_seconds)
        return False
    except Exception as exc:
        # Sanitize log output to ensure no raw credentials or parameters are exposed
        logger.warning("Database readiness probe failed: %s", type(exc).__name__)
        return False
