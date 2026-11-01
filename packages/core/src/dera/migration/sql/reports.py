"""SQL Migration Artifact and Summary Models.

Defines the top-level reviewable contract for Phase 9.4.
"""

from typing import List, Optional
from pydantic import BaseModel, Field

from dera.migration.sql.enums import SqlDialectType, SqlGenerationStatus
from dera.migration.sql.models import (
    GeneratedSqlStatement,
    PreflightCheck,
    RollbackStatement,
    TransactionBlock,
)
from dera.migration.sql.validation import ValidationIssue


class SqlArtifactSummary(BaseModel):
    """Metrics summarizing the generated SQL artifact."""
    total_statements: int
    destructive_statements: int
    review_required_statements: int
    transaction_blocks_count: int
    preflight_checks_count: int
    rollback_statements_count: int
    validation_issues_count: int


class SqlMigrationArtifact(BaseModel):
    """Complete, immutable SQL migration artifact generated for review."""
    artifact_id: str
    source_plan_id: str
    source_plan_fingerprint: str
    dialect: SqlDialectType
    target_engine: str
    compiler_version: str = "1.0.0"
    status: SqlGenerationStatus
    artifact_fingerprint: str

    summary: SqlArtifactSummary
    rendered_sql_script: str
    statements: List[GeneratedSqlStatement] = Field(default_factory=list)
    transaction_blocks: List[TransactionBlock] = Field(default_factory=list)
    preflight_checks: List[PreflightCheck] = Field(default_factory=list)
    rollback_statements: List[RollbackStatement] = Field(default_factory=list)
    validation_issues: List[ValidationIssue] = Field(default_factory=list)

    execution_notice: str = "GENERATED FOR REVIEW — NOT EXECUTED"
    limitations: List[str] = Field(default_factory=list)
