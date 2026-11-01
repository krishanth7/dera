"""Phase 9.4 SQL Generation Domain Models.

Defines generated statement records, transaction blocks, preflight checks,
rollback statements, and validation requirements.
"""

from pydantic import BaseModel, Field

from dera.migration.enums import ReviewPriority
from dera.migration.planning.enums import MigrationOperationType
from dera.migration.sql.enums import (
    RollbackFeasibility,
    SqlDialectType,
    TransactionExecutionMode,
)


class PreflightCheck(BaseModel):
    """Advisory preflight check to verify prior to script execution."""

    check_id: str
    description: str
    target_object: str
    suggested_verification_sql: str | None = None
    is_blocking: bool = False


class RollbackStatement(BaseModel):
    """Advisory rollback SQL statement."""

    statement_id: str
    sql: str
    feasibility: RollbackFeasibility
    assumptions: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


class GeneratedSqlStatement(BaseModel):
    """Single rendered SQL statement with full traceability to source operation."""

    statement_id: str
    source_operation_id: str
    source_operation_type: MigrationOperationType
    target_object_id: str
    target_object_name: str
    sql: str
    dialect: SqlDialectType
    execution_mode: TransactionExecutionMode = TransactionExecutionMode.TRANSACTIONAL
    is_destructive: bool = False
    requires_manual_review: bool = False
    review_reasons: list[str] = Field(default_factory=list)
    review_priority: ReviewPriority = ReviewPriority.P4_LOW
    statement_fingerprint: str
    preflight_checks: list[PreflightCheck] = Field(default_factory=list)
    rollback_statement: RollbackStatement | None = None


class TransactionBlock(BaseModel):
    """Logical grouping of statements executed together in a transaction."""

    block_id: str
    block_order: int
    execution_mode: TransactionExecutionMode
    statement_ids: list[str] = Field(default_factory=list)
    rendered_block_sql: str
