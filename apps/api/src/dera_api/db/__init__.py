"""DERA Database — Platform PostgreSQL Infrastructure & Persistence Layer.

Provides SQLAlchemy 2.x declarative models, async engine creation, connection pooling,
session management, health verification, and exception mapping for DERA's platform database.
"""

from dera_api.db.base import POSTGRES_NAMING_CONVENTION, Base
from dera_api.db.dependencies import get_db_session
from dera_api.db.engine import create_database_engine, dispose_database_engine
from dera_api.db.exceptions import (
    DatabaseConnectionError,
    DatabaseConstraintViolationError,
    DatabaseError,
    DatabaseMigrationMismatchError,
    DatabaseTimeoutError,
    map_database_exception,
    sanitize_database_error_message,
)
from dera_api.db.health import check_database_health
from dera_api.db.models.platform import PlatformMetadata
from dera_api.db.session import (
    create_session_factory,
    session_scope,
    transaction_scope,
)

__all__ = [
    "Base",
    "POSTGRES_NAMING_CONVENTION",
    "create_database_engine",
    "dispose_database_engine",
    "create_session_factory",
    "transaction_scope",
    "session_scope",
    "get_db_session",
    "check_database_health",
    "PlatformMetadata",
    "DatabaseError",
    "DatabaseConnectionError",
    "DatabaseTimeoutError",
    "DatabaseConstraintViolationError",
    "DatabaseMigrationMismatchError",
    "map_database_exception",
    "sanitize_database_error_message",
]
