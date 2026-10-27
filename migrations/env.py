"""DERA Database — Alembic Migration Environment.

Configures deterministic schema migrations for the DERA platform database
using SQLAlchemy 2.x async engine execution and explicit metadata discovery.
"""

import asyncio
import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# Ensure package roots are accessible to alembic import resolution
_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_api_src = os.path.join(_root, "apps", "api", "src")
_core_src = os.path.join(_root, "packages", "core", "src")
for p in (_root, _api_src, _core_src):
    if p not in sys.path:
        sys.path.insert(0, p)

# Import authoritative model metadata
# Ensure all models are registered onto Base.metadata
import dera_api.db.models  # noqa: F401
from dera_api.core.config import get_settings
from dera_api.db.base import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def get_platform_database_url() -> str:
    """Resolve the platform database URL dynamically from environment or settings."""
    env_url = os.getenv("DERA_PLATFORM_DATABASE_URL")
    if env_url and env_url.strip():
        return env_url.strip()

    try:
        settings = get_settings()
        if settings.has_database_configured:
            return settings.database_url
    except Exception:
        pass

    # Default fallback for testing or offline generation
    return "postgresql+asyncpg://dera_user:dera_password@localhost:5432/dera_platform"


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode without an active database connection."""
    url = get_platform_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Execute migrations on an established synchronous connection."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in 'online' mode using SQLAlchemy AsyncEngine."""
    url = get_platform_database_url()
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = url

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Entrypoint for online migration execution."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
