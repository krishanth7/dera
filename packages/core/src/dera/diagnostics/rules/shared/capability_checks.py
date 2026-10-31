"""Engine capability matrix for index and constraint diagnostics.

Provides deterministic capability checks across supported relational engines:
PostgreSQL, Supabase PostgreSQL, SQLite, MySQL, and MariaDB.
"""

from __future__ import annotations


def normalize_engine_name(engine: str | None) -> str:
    """Normalizes database engine identifier to lowercase canonical key."""
    if not engine:
        return "unknown"
    clean = engine.strip().lower()
    if "postgres" in clean or "supabase" in clean:
        return "postgresql"
    if "sqlite" in clean:
        return "sqlite"
    if "mariadb" in clean:
        return "mariadb"
    if "mysql" in clean:
        return "mysql"
    return clean


def engine_automatically_indexes_foreign_keys(engine: str | None) -> bool:
    """Returns True if the engine automatically requires/creates supporting indexes for FKs.

    MySQL and MariaDB (InnoDB storage engine) automatically create an index on the
    referencing foreign key columns if an appropriate index does not already exist.
    PostgreSQL and SQLite do not automatically index referencing columns.
    """
    eng = normalize_engine_name(engine)
    return eng in ("mysql", "mariadb")


def engine_supports_partial_indexes(engine: str | None) -> bool:
    """Returns True if the database engine supports partial indexes with WHERE predicates."""
    eng = normalize_engine_name(engine)
    return eng in ("postgresql", "sqlite")


def engine_supports_expression_indexes(engine: str | None) -> bool:
    """Returns True if the database engine supports functional/expression indexes."""
    eng = normalize_engine_name(engine)
    return eng in ("postgresql", "sqlite", "mysql")


def engine_enforces_check_constraints(engine: str | None) -> bool:
    """Returns True if the database engine reliably enforces CHECK constraint predicates."""
    eng = normalize_engine_name(engine)
    # MySQL only began enforcing CHECK in 8.0.16; MariaDB in 10.2.1; SQLite in 3.3.0
    return eng in ("postgresql", "sqlite", "mysql", "mariadb")


engine_supports_check_constraints = engine_enforces_check_constraints

__all__ = [
    "normalize_engine_name",
    "engine_automatically_indexes_foreign_keys",
    "engine_supports_partial_indexes",
    "engine_supports_expression_indexes",
    "engine_enforces_check_constraints",
    "engine_supports_check_constraints",
]
