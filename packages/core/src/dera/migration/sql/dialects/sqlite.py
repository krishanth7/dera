"""SQLite Dialect SQL Renderer.

Renders verified abstract migration operations into SQLite syntax.
Accounts for SQLite DDL limitations:
- Direct ALTER TABLE DROP COLUMN requires SQLite >= 3.35.0.
- ALTER COLUMN TYPE / ALTER COLUMN NULLABILITY / ADD FOREIGN KEY cannot be done via ALTER TABLE;
  they require table rebuild or are marked conditional/unsupported.
"""

import hashlib

from dera.migration.planning.enums import EngineCapabilityState, MigrationOperationType
from dera.migration.planning.models import AbstractMigrationOperation
from dera.migration.sql.dialects.base import DialectRenderer
from dera.migration.sql.enums import (
    RollbackFeasibility,
    SqlDialectType,
    TransactionExecutionMode,
)
from dera.migration.sql.identifiers import IdentifierQuoter
from dera.migration.sql.models import (
    GeneratedSqlStatement,
    RollbackStatement,
)


class SqliteRenderer(DialectRenderer):
    """SQLite dialect compiler."""

    @property
    def dialect(self) -> SqlDialectType:
        return SqlDialectType.SQLITE

    def render_operation(
        self,
        operation: AbstractMigrationOperation,
        target_version: str | None = None,
    ) -> list[GeneratedSqlStatement]:
        op_type = operation.operation_type

        # Check unsupported ops
        if operation.engine_capability == EngineCapabilityState.UNSUPPORTED:
            # Emit comment explaining requirement for 12-step table recreation
            return [self._make_unsupported_statement(operation)]

        if op_type == MigrationOperationType.CREATE_TABLE:
            return self._render_create_table(operation)
        elif op_type == MigrationOperationType.DROP_TABLE:
            return self._render_drop_table(operation)
        elif op_type == MigrationOperationType.ADD_COLUMN:
            return self._render_add_column(operation)
        elif op_type == MigrationOperationType.DROP_COLUMN:
            return self._render_drop_column(operation)
        elif op_type == MigrationOperationType.CREATE_INDEX:
            return self._render_create_index(operation)
        elif op_type == MigrationOperationType.DROP_INDEX:
            return self._render_drop_index(operation)
        elif op_type == MigrationOperationType.CREATE_VIEW:
            return self._render_create_view(operation)
        elif op_type == MigrationOperationType.DROP_VIEW:
            return self._render_drop_view(operation)

        return [self._make_unsupported_statement(operation)]

    def _make_statement(
        self,
        op: AbstractMigrationOperation,
        sql: str,
        rollback: RollbackStatement | None = None,
        requires_review: bool = False,
        review_reasons: list[str] | None = None,
    ) -> GeneratedSqlStatement:
        clean_sql = sql.strip()
        if not clean_sql.endswith(";"):
            clean_sql += ";"

        fp = hashlib.sha256(clean_sql.encode("utf-8")).hexdigest()
        stmt_id = f"stmt_{fp[:16]}"

        reasons = list(review_reasons or [])
        if op.is_destructive:
            reasons.append("Destructive schema operation on SQLite.")
            requires_review = True

        return GeneratedSqlStatement(
            statement_id=stmt_id,
            source_operation_id=op.operation_id,
            source_operation_type=op.operation_type,
            target_object_id=op.target_object_id,
            target_object_name=op.target_object_name,
            sql=clean_sql,
            dialect=self.dialect,
            execution_mode=TransactionExecutionMode.TRANSACTIONAL,
            is_destructive=op.is_destructive,
            requires_manual_review=requires_review,
            review_reasons=reasons,
            review_priority=op.review_priority,
            statement_fingerprint=fp,
            rollback_statement=rollback,
        )

    def _make_unsupported_statement(self, op: AbstractMigrationOperation) -> GeneratedSqlStatement:
        sql = f"-- Operation {op.operation_type.value} on {op.target_object_name} is unsupported via direct ALTER TABLE on SQLite. Full table rebuild required."
        return self._make_statement(
            op,
            sql,
            requires_review=True,
            review_reasons=[
                f"Operation {op.operation_type.value} requires 12-step table recreation procedure on SQLite."
            ],
        )

    def _render_create_table(self, op: AbstractMigrationOperation) -> list[GeneratedSqlStatement]:
        tbl = IdentifierQuoter.quote_identifier(op.target_object_name, self.dialect)
        sql = f"CREATE TABLE IF NOT EXISTS {tbl} (id INTEGER PRIMARY KEY);"
        rb = RollbackStatement(
            statement_id=f"rb_{op.operation_id}",
            sql=f"DROP TABLE IF EXISTS {tbl};",
            feasibility=RollbackFeasibility.AVAILABLE_UNDER_CONDITIONS,
        )
        return [self._make_statement(op, sql, rollback=rb)]

    def _render_drop_table(self, op: AbstractMigrationOperation) -> list[GeneratedSqlStatement]:
        tbl = IdentifierQuoter.quote_identifier(op.target_object_name, self.dialect)
        sql = f"DROP TABLE IF EXISTS {tbl};"
        rb = RollbackStatement(
            statement_id=f"rb_{op.operation_id}",
            sql=f"-- Restore data and table structure from backup for '{op.target_object_name}'.",
            feasibility=RollbackFeasibility.REQUIRES_PRESERVED_DATA,
        )
        return [self._make_statement(op, sql, rollback=rb)]

    def _render_add_column(self, op: AbstractMigrationOperation) -> list[GeneratedSqlStatement]:
        tbl = IdentifierQuoter.quote_identifier(op.table_name or "table", self.dialect)
        col = IdentifierQuoter.quote_identifier(op.target_object_name, self.dialect)
        col_type = op.operation_properties.get("type", {}).get("after", "TEXT")
        sql = f"ALTER TABLE {tbl} ADD COLUMN {col} {col_type};"
        return [self._make_statement(op, sql)]

    def _render_drop_column(self, op: AbstractMigrationOperation) -> list[GeneratedSqlStatement]:
        tbl = IdentifierQuoter.quote_identifier(op.table_name or "table", self.dialect)
        col = IdentifierQuoter.quote_identifier(op.target_object_name, self.dialect)
        sql = f"ALTER TABLE {tbl} DROP COLUMN {col};"
        return [
            self._make_statement(
                op,
                sql,
                requires_review=True,
                review_reasons=["SQLite DROP COLUMN requires SQLite >= 3.35.0."],
            )
        ]

    def _render_create_index(self, op: AbstractMigrationOperation) -> list[GeneratedSqlStatement]:
        tbl = IdentifierQuoter.quote_identifier(op.table_name or "table", self.dialect)
        idx = IdentifierQuoter.quote_identifier(op.target_object_name, self.dialect)
        sql = f"CREATE INDEX IF NOT EXISTS {idx} ON {tbl} ();"
        rb = RollbackStatement(
            statement_id=f"rb_{op.operation_id}",
            sql=f"DROP INDEX IF EXISTS {idx};",
            feasibility=RollbackFeasibility.AVAILABLE_UNDER_CONDITIONS,
        )
        return [self._make_statement(op, sql, rollback=rb)]

    def _render_drop_index(self, op: AbstractMigrationOperation) -> list[GeneratedSqlStatement]:
        idx = IdentifierQuoter.quote_identifier(op.target_object_name, self.dialect)
        sql = f"DROP INDEX IF EXISTS {idx};"
        return [self._make_statement(op, sql)]

    def _render_create_view(self, op: AbstractMigrationOperation) -> list[GeneratedSqlStatement]:
        view = IdentifierQuoter.quote_identifier(op.target_object_name, self.dialect)
        sql = f"CREATE VIEW IF NOT EXISTS {view} AS SELECT 1;"
        return [self._make_statement(op, sql)]

    def _render_drop_view(self, op: AbstractMigrationOperation) -> list[GeneratedSqlStatement]:
        view = IdentifierQuoter.quote_identifier(op.target_object_name, self.dialect)
        sql = f"DROP VIEW IF EXISTS {view};"
        return [self._make_statement(op, sql)]
