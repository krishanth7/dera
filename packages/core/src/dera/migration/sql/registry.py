"""Dialect Registry for Phase 9.4.

Resolves dialect renderers deterministically for target database engines.
"""

from dera.migration.sql.dialects.base import DialectRenderer
from dera.migration.sql.dialects.mysql import MysqlRenderer
from dera.migration.sql.dialects.postgresql import PostgresqlRenderer
from dera.migration.sql.dialects.sqlite import SqliteRenderer
from dera.migration.sql.enums import SqlDialectType


class DialectRegistry:
    """Deterministic lookup registry for SQL dialect compilers."""

    _REGISTRY: dict[str, DialectRenderer] = {
        "postgresql": PostgresqlRenderer(is_supabase=False),
        "postgres": PostgresqlRenderer(is_supabase=False),
        "supabase": PostgresqlRenderer(is_supabase=True),
        "sqlite": SqliteRenderer(),
        "mysql": MysqlRenderer(is_mariadb=False),
        "mariadb": MysqlRenderer(is_mariadb=True),
    }

    @classmethod
    def get_renderer(cls, engine: str) -> DialectRenderer:
        """Resolve dialect compiler for database engine string."""
        norm_engine = engine.strip().lower()
        if norm_engine not in cls._REGISTRY:
            raise ValueError(f"Unsupported or unregistered SQL engine dialect: '{engine}'.")
        return cls._REGISTRY[norm_engine]

    @classmethod
    def map_to_dialect_type(cls, engine: str) -> SqlDialectType:
        """Map engine string to SqlDialectType enum."""
        norm_engine = engine.strip().lower()
        if norm_engine in ("postgresql", "postgres"):
            return SqlDialectType.POSTGRESQL
        elif norm_engine == "supabase":
            return SqlDialectType.SUPABASE
        elif norm_engine == "sqlite":
            return SqlDialectType.SQLITE
        elif norm_engine == "mysql":
            return SqlDialectType.MYSQL
        elif norm_engine == "mariadb":
            return SqlDialectType.MARIADB
        raise ValueError(f"Cannot resolve SqlDialectType for '{engine}'.")
