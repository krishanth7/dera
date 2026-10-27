"""DERA Database — Declarative Base & Naming Conventions.

Defines the SQLAlchemy 2.x DeclarativeBase for all platform database models
with deterministic, dialect-agnostic PostgreSQL naming conventions for
indexes, unique constraints, check constraints, foreign keys, and primary keys.
"""

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

# Authoritative deterministic PostgreSQL constraint and index naming convention
# Ensures migrations and DDL produce deterministic constraint names across environments
POSTGRES_NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

platform_metadata = MetaData(naming_convention=POSTGRES_NAMING_CONVENTION)


class Base(DeclarativeBase):
    """Authoritative SQLAlchemy 2.x Declarative Base for DERA Platform Database."""

    metadata = platform_metadata
