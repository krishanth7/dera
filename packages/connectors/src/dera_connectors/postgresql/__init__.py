"""DERA PostgreSQL Connector — High-Performance, Read-Only Database Introspection.

Provides the production-oriented PostgreSQL and Supabase PostgreSQL connector adapter,
configuration models, connection lifecycle manager, and system catalog queries.
"""

from dera_connectors.postgresql.adapter import PostgresConnector
from dera_connectors.postgresql.capabilities import get_postgres_capabilities
from dera_connectors.postgresql.configuration import (
    PostgresConnectorConfig,
    SupabasePoolerMode,
    is_supabase_host,
)
from dera_connectors.postgresql.connection import (
    PostgresConnectionManager,
    create_postgres_ssl_context,
)
from dera_connectors.postgresql.errors import map_postgres_error

__all__ = [
    "PostgresConnector",
    "PostgresConnectorConfig",
    "SupabasePoolerMode",
    "is_supabase_host",
    "PostgresConnectionManager",
    "create_postgres_ssl_context",
    "map_postgres_error",
    "get_postgres_capabilities",
]
