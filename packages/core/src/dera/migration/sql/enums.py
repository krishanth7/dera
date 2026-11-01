"""Phase 9.4 Migration SQL Generation Enums.

Defines deterministic enumeration types for SQL generation status, supported dialects,
transaction execution modes, and rollback feasibility.
"""

from enum import Enum


class SqlDialectType(str, Enum):
    """Supported SQL dialect targets."""
    POSTGRESQL = "POSTGRESQL"
    SUPABASE = "SUPABASE"
    SQLITE = "SQLITE"
    MYSQL = "MYSQL"
    MARIADB = "MARIADB"


class SqlGenerationStatus(str, Enum):
    """Overall status of SQL generation."""
    GENERATED = "GENERATED"
    GENERATED_WITH_REVIEW_REQUIRED = "GENERATED_WITH_REVIEW_REQUIRED"
    PARTIAL = "PARTIAL"
    BLOCKED = "BLOCKED"
    UNSUPPORTED = "UNSUPPORTED"
    VALIDATION_FAILED = "VALIDATION_FAILED"


class TransactionExecutionMode(str, Enum):
    """Transaction wrapping mode for generated statements."""
    TRANSACTIONAL = "TRANSACTIONAL"
    NON_TRANSACTIONAL = "NON_TRANSACTIONAL"
    IMPLICIT_COMMIT = "IMPLICIT_COMMIT"


class RollbackFeasibility(str, Enum):
    """Feasibility classification for generating safe rollback SQL."""
    AVAILABLE_UNDER_CONDITIONS = "AVAILABLE_UNDER_CONDITIONS"
    REQUIRES_PRESERVED_DATA = "REQUIRES_PRESERVED_DATA"
    MANUAL_REVIEW_REQUIRED = "MANUAL_REVIEW_REQUIRED"
    UNSUPPORTED = "UNSUPPORTED"
    INDETERMINATE = "INDETERMINATE"
