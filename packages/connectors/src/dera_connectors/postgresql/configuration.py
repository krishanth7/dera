"""DERA PostgreSQL Connector — Typed Configuration & Supabase Pooler Modes.

Defines immutable, strongly-typed connection configuration for standard PostgreSQL
and Supabase-hosted PostgreSQL instances, with automatic pooler-mode detection,
statement timeout bounds, and TLS certificate bindings.
"""

from enum import StrEnum
from typing import Any
from urllib.parse import urlparse

from pydantic import ConfigDict, Field, model_validator

from dera_connectors.configuration import ConnectorConfig
from dera_connectors.engine import DatabaseEngine, DatabaseProvider


def is_supabase_host(host: str | None) -> bool:
    """Safely check if host matches Supabase domains (*.supabase.co, *.pooler.supabase.com).

    Parses the host URL/authority to prevent incomplete URL substring sanitization (CWE-20).
    """
    if not host:
        return False
    raw_host = host.strip()
    if not raw_host:
        return False

    parse_target = raw_host if "://" in raw_host else f"//{raw_host}"
    try:
        parsed = urlparse(parse_target)
        hostname = (parsed.hostname or "").lower().rstrip(".")
    except Exception:
        return False

    if not hostname:
        return False

    return (
        hostname == "supabase.co"
        or hostname.endswith(".supabase.co")
        or hostname == "pooler.supabase.com"
        or hostname.endswith(".pooler.supabase.com")
    )


class SupabasePoolerMode(StrEnum):
    """Supabase connection interface and pooler routing modes."""

    DIRECT = "direct"
    SESSION = "session"
    TRANSACTION = "transaction"


class PostgresConnectorConfig(ConnectorConfig):
    """Typed connection configuration for PostgreSQL and Supabase PostgreSQL instances."""

    model_config = ConfigDict(frozen=True)

    engine: DatabaseEngine = Field(
        default=DatabaseEngine.POSTGRESQL,
        description="Database engine type (must be DatabaseEngine.POSTGRESQL).",
    )
    provider: DatabaseProvider = Field(
        default=DatabaseProvider.GENERIC,
        description="Deployment provider (GENERIC, SUPABASE, AWS_RDS, etc.).",
    )
    application_name: str = Field(
        default="DERA_Connector_v5.2",
        max_length=64,
        description="PostgreSQL application_name identifying connection sessions in pg_stat_activity.",
    )
    statement_timeout_ms: int = Field(
        default=30000,
        ge=1000,
        le=600000,
        description="Session statement_timeout in milliseconds applied immediately on connection.",
    )
    supabase_pooler_mode: SupabasePoolerMode = Field(
        default=SupabasePoolerMode.DIRECT,
        description="Supabase connection topology mode: direct (5432), session pooler (6543), or transaction pooler (6543).",
    )
    statement_cache_size: int = Field(
        default=100,
        ge=0,
        description="Prepared statement cache size. Must be 0 for transaction pooler mode.",
    )

    @model_validator(mode="after")
    def _validate_postgres_and_supabase(self) -> "PostgresConnectorConfig":
        """Enforce PostgreSQL engine constraints and detect Supabase provider/pooler settings."""
        if self.engine != DatabaseEngine.POSTGRESQL:
            object.__setattr__(self, "engine", DatabaseEngine.POSTGRESQL)

        # Set default port for Supabase poolers
        if self.supabase_pooler_mode in (
            SupabasePoolerMode.SESSION,
            SupabasePoolerMode.TRANSACTION,
        ) and (self.port is None or self.port == 5432):
            object.__setattr__(self, "port", 6543)
        elif self.port is None:
            object.__setattr__(self, "port", 5432)

        # Auto-detect Supabase provider from host domain if generic
        if self.provider == DatabaseProvider.GENERIC and is_supabase_host(self.host):
            object.__setattr__(self, "provider", DatabaseProvider.SUPABASE)

        # Transaction poolers (e.g. Supabase PgBouncer) reject server-side prepared statements
        if self.supabase_pooler_mode == SupabasePoolerMode.TRANSACTION:
            if self.statement_cache_size != 0:
                object.__setattr__(self, "statement_cache_size", 0)

        return self

    def build_asyncpg_kwargs(self) -> dict[str, Any]:
        """Construct dictionary of keyword arguments suitable for asyncpg.connect()."""
        kwargs: dict[str, Any] = {
            "host": self.host or "127.0.0.1",
            "port": self.port or 5432,
            "database": self.database,
            "user": self.username,
            "timeout": self.timeouts.connect_timeout_seconds,
            "command_timeout": self.timeouts.query_timeout_seconds,
            "server_settings": {
                "application_name": self.application_name,
                "statement_timeout": str(self.statement_timeout_ms),
            },
            "statement_cache_size": self.statement_cache_size,
        }

        if self.password is not None:
            kwargs["password"] = self.password.get_secret_value()

        return kwargs
