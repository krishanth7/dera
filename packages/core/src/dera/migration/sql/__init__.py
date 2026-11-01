"""Phase 9.4 Migration SQL Generation and Validation Package.

Provides deterministic, dialect-aware SQL migration generation, identifier quoting,
transaction planning, offline validation, and review-only artifact reporting.
"""

from dera.migration.sql.enums import (
    RollbackFeasibility,
    SqlDialectType,
    SqlGenerationStatus,
    TransactionExecutionMode,
)
from dera.migration.sql.models import (
    GeneratedSqlStatement,
    PreflightCheck,
    RollbackStatement,
    TransactionBlock,
)
from dera.migration.sql.identifiers import IdentifierQuoter
from dera.migration.sql.registry import DialectRegistry
from dera.migration.sql.transaction_planner import TransactionPlanner
from dera.migration.sql.validation import SqlValidator, ValidationIssue
from dera.migration.sql.fingerprint import SqlFingerprintCalculator
from dera.migration.sql.reports import SqlArtifactSummary, SqlMigrationArtifact
from dera.migration.sql.compiler import SqlMigrationCompiler

__all__ = [
    "DialectRegistry",
    "GeneratedSqlStatement",
    "IdentifierQuoter",
    "PreflightCheck",
    "RollbackFeasibility",
    "RollbackStatement",
    "SqlArtifactSummary",
    "SqlDialectType",
    "SqlFingerprintCalculator",
    "SqlGenerationStatus",
    "SqlMigrationArtifact",
    "SqlMigrationCompiler",
    "SqlValidator",
    "TransactionBlock",
    "TransactionExecutionMode",
    "TransactionPlanner",
    "ValidationIssue",
]
