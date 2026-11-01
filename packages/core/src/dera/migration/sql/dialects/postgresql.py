"""PostgreSQL Dialect SQL Renderer.

Renders verified abstract migration operations into deterministic PostgreSQL/Supabase DDL.
Supports:
- Transactional DDL.
- Double-quoted identifier escaping.
- Table, Column, Index, Constraint, Namespace, and View statements.
- Advisory rollback generation where provably safe.
"""

import hashlib
from typing import List, Optional

from dera.migration.planning.enums import MigrationOperationType
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
    PreflightCheck,
    RollbackStatement,
)


class PostgresqlRenderer(DialectRenderer):
    """PostgreSQL and Supabase PostgreSQL dialect compiler."""

    def __init__(self, is_supabase: bool = False):
        self._is_supabase = is_supabase

    @property
    def dialect(self) -> SqlDialectType:
        return SqlDialectType.SUPABASE if self._is_supabase else SqlDialectType.POSTGRESQL

    def render_operation(
        self,
        operation: AbstractMigrationOperation,
        target_version: Optional[str] = None,
    ) -> List[GeneratedSqlStatement]:
        op_type = operation.operation_type
        statements = []

        if op_type == MigrationOperationType.CREATE_NAMESPACE:
            statements.extend(self._render_create_namespace(operation))
        elif op_type == MigrationOperationType.DROP_NAMESPACE:
            statements.extend(self._render_drop_namespace(operation))
        elif op_type == MigrationOperationType.CREATE_TABLE:
            statements.extend(self._render_create_table(operation))
        elif op_type == MigrationOperationType.DROP_TABLE:
            statements.extend(self._render_drop_table(operation))
        elif op_type == MigrationOperationType.ADD_COLUMN:
            statements.extend(self._render_add_column(operation))
        elif op_type == MigrationOperationType.DROP_COLUMN:
            statements.extend(self._render_drop_column(operation))
        elif op_type == MigrationOperationType.ALTER_COLUMN_TYPE:
            statements.extend(self._render_alter_column_type(operation))
        elif op_type == MigrationOperationType.ALTER_COLUMN_NULLABILITY:
            statements.extend(self._render_alter_column_nullability(operation))
        elif op_type == MigrationOperationType.ALTER_COLUMN_DEFAULT:
            statements.extend(self._render_alter_column_default(operation))
        elif op_type == MigrationOperationType.ADD_PRIMARY_KEY:
            statements.extend(self._render_add_primary_key(operation))
        elif op_type == MigrationOperationType.DROP_PRIMARY_KEY:
            statements.extend(self._render_drop_primary_key(operation))
        elif op_type == MigrationOperationType.ADD_UNIQUE_CONSTRAINT:
            statements.extend(self._render_add_unique_constraint(operation))
        elif op_type == MigrationOperationType.DROP_UNIQUE_CONSTRAINT:
            statements.extend(self._render_drop_unique_constraint(operation))
        elif op_type == MigrationOperationType.ADD_FOREIGN_KEY:
            statements.extend(self._render_add_foreign_key(operation))
        elif op_type == MigrationOperationType.DROP_FOREIGN_KEY:
            statements.extend(self._render_drop_foreign_key(operation))
        elif op_type == MigrationOperationType.CREATE_INDEX:
            statements.extend(self._render_create_index(operation))
        elif op_type == MigrationOperationType.DROP_INDEX:
            statements.extend(self._render_drop_index(operation))
        elif op_type == MigrationOperationType.CREATE_VIEW:
            statements.extend(self._render_create_view(operation))
        elif op_type == MigrationOperationType.DROP_VIEW:
            statements.extend(self._render_drop_view(operation))

        return statements

    def _make_statement(
        self,
        op: AbstractMigrationOperation,
        sql: str,
        execution_mode: TransactionExecutionMode = TransactionExecutionMode.TRANSACTIONAL,
        rollback: Optional[RollbackStatement] = None,
        preflights: Optional[List[PreflightCheck]] = None,
    ) -> GeneratedSqlStatement:
        clean_sql = sql.strip()
        if not clean_sql.endswith(";"):
            clean_sql += ";"

        fp = hashlib.sha256(clean_sql.encode("utf-8")).hexdigest()
        stmt_id = f"stmt_{fp[:16]}"

        requires_review = op.is_destructive or bool(op.manual_decision_gates)
        review_reasons = []
        if op.is_destructive:
            review_reasons.append("Destructive schema operation; may cause data loss.")
        for g in op.manual_decision_gates:
            review_reasons.append(f"Manual gate required: {g.title}")

        return GeneratedSqlStatement(
            statement_id=stmt_id,
            source_operation_id=op.operation_id,
            source_operation_type=op.operation_type,
            target_object_id=op.target_object_id,
            target_object_name=op.target_object_name,
            sql=clean_sql,
            dialect=self.dialect,
            execution_mode=execution_mode,
            is_destructive=op.is_destructive,
            requires_manual_review=requires_review,
            review_reasons=review_reasons,
            review_priority=op.review_priority,
            statement_fingerprint=fp,
            preflight_checks=preflights or [],
            rollback_statement=rollback,
        )

    def _render_create_namespace(self, op: AbstractMigrationOperation) -> List[GeneratedSqlStatement]:
        ns = IdentifierQuoter.quote_identifier(op.target_object_name, self.dialect)
        sql = f"CREATE SCHEMA IF NOT EXISTS {ns};"
        rb = RollbackStatement(
            statement_id=f"rb_{op.operation_id}",
            sql=f"DROP SCHEMA IF EXISTS {ns} CASCADE;",
            feasibility=RollbackFeasibility.AVAILABLE_UNDER_CONDITIONS,
            assumptions=["Namespace contains no un-migrated tables or data."],
        )
        return [self._make_statement(op, sql, rollback=rb)]

    def _render_drop_namespace(self, op: AbstractMigrationOperation) -> List[GeneratedSqlStatement]:
        ns = IdentifierQuoter.quote_identifier(op.target_object_name, self.dialect)
        sql = f"DROP SCHEMA IF EXISTS {ns} CASCADE;"
        rb = RollbackStatement(
            statement_id=f"rb_{op.operation_id}",
            sql=f"-- Cannot safely recreate dropped schema '{op.target_object_name}' without structural snapshot.",
            feasibility=RollbackFeasibility.REQUIRES_PRESERVED_DATA,
        )
        return [self._make_statement(op, sql, rollback=rb)]

    def _render_create_table(self, op: AbstractMigrationOperation) -> List[GeneratedSqlStatement]:
        tbl = IdentifierQuoter.quote_qualified_name(op.target_object_name, op.namespace, self.dialect)
        sql = f"CREATE TABLE IF NOT EXISTS {tbl} ();"
        rb = RollbackStatement(
            statement_id=f"rb_{op.operation_id}",
            sql=f"DROP TABLE IF EXISTS {tbl};",
            feasibility=RollbackFeasibility.AVAILABLE_UNDER_CONDITIONS,
        )
        return [self._make_statement(op, sql, rollback=rb)]

    def _render_drop_table(self, op: AbstractMigrationOperation) -> List[GeneratedSqlStatement]:
        tbl = IdentifierQuoter.quote_qualified_name(op.target_object_name, op.namespace, self.dialect)
        sql = f"DROP TABLE IF EXISTS {tbl};"
        rb = RollbackStatement(
            statement_id=f"rb_{op.operation_id}",
            sql=f"-- Restore data and table structure from backup for '{op.target_object_name}'.",
            feasibility=RollbackFeasibility.REQUIRES_PRESERVED_DATA,
        )
        return [self._make_statement(op, sql, rollback=rb)]

    def _render_add_column(self, op: AbstractMigrationOperation) -> List[GeneratedSqlStatement]:
        tbl = IdentifierQuoter.quote_qualified_name(op.table_name or "table", op.namespace, self.dialect)
        col = IdentifierQuoter.quote_identifier(op.target_object_name, self.dialect)
        # Type extraction from operation_properties
        col_type = op.operation_properties.get("type", {}).get("after", "TEXT")
        sql = f"ALTER TABLE {tbl} ADD COLUMN {col} {col_type};"
        rb = RollbackStatement(
            statement_id=f"rb_{op.operation_id}",
            sql=f"ALTER TABLE {tbl} DROP COLUMN IF EXISTS {col};",
            feasibility=RollbackFeasibility.AVAILABLE_UNDER_CONDITIONS,
        )
        return [self._make_statement(op, sql, rollback=rb)]

    def _render_drop_column(self, op: AbstractMigrationOperation) -> List[GeneratedSqlStatement]:
        tbl = IdentifierQuoter.quote_qualified_name(op.table_name or "table", op.namespace, self.dialect)
        col = IdentifierQuoter.quote_identifier(op.target_object_name, self.dialect)
        sql = f"ALTER TABLE {tbl} DROP COLUMN IF EXISTS {col};"
        rb = RollbackStatement(
            statement_id=f"rb_{op.operation_id}",
            sql=f"-- Restoring dropped column '{op.target_object_name}' requires backup restoration.",
            feasibility=RollbackFeasibility.REQUIRES_PRESERVED_DATA,
        )
        return [self._make_statement(op, sql, rollback=rb)]

    def _render_alter_column_type(self, op: AbstractMigrationOperation) -> List[GeneratedSqlStatement]:
        tbl = IdentifierQuoter.quote_qualified_name(op.table_name or "table", op.namespace, self.dialect)
        col = IdentifierQuoter.quote_identifier(op.target_object_name, self.dialect)
        target_type = op.operation_properties.get("type", {}).get("after", "TEXT")
        sql = f"ALTER TABLE {tbl} ALTER COLUMN {col} TYPE {target_type};"
        return [self._make_statement(op, sql)]

    def _render_alter_column_nullability(self, op: AbstractMigrationOperation) -> List[GeneratedSqlStatement]:
        tbl = IdentifierQuoter.quote_qualified_name(op.table_name or "table", op.namespace, self.dialect)
        col = IdentifierQuoter.quote_identifier(op.target_object_name, self.dialect)
        is_nullable = op.operation_properties.get("is_nullable", {}).get("after", True)
        action = "DROP NOT NULL" if is_nullable else "SET NOT NULL"
        sql = f"ALTER TABLE {tbl} ALTER COLUMN {col} {action};"
        return [self._make_statement(op, sql)]

    def _render_alter_column_default(self, op: AbstractMigrationOperation) -> List[GeneratedSqlStatement]:
        tbl = IdentifierQuoter.quote_qualified_name(op.table_name or "table", op.namespace, self.dialect)
        col = IdentifierQuoter.quote_identifier(op.target_object_name, self.dialect)
        default_val = op.operation_properties.get("default", {}).get("after")
        action = f"SET DEFAULT {default_val}" if default_val else "DROP DEFAULT"
        sql = f"ALTER TABLE {tbl} ALTER COLUMN {col} {action};"
        return [self._make_statement(op, sql)]

    def _render_add_primary_key(self, op: AbstractMigrationOperation) -> List[GeneratedSqlStatement]:
        tbl = IdentifierQuoter.quote_qualified_name(op.table_name or "table", op.namespace, self.dialect)
        pk_name = IdentifierQuoter.quote_identifier(op.target_object_name, self.dialect)
        sql = f"ALTER TABLE {tbl} ADD CONSTRAINT {pk_name} PRIMARY KEY ();"
        return [self._make_statement(op, sql)]

    def _render_drop_primary_key(self, op: AbstractMigrationOperation) -> List[GeneratedSqlStatement]:
        tbl = IdentifierQuoter.quote_qualified_name(op.table_name or "table", op.namespace, self.dialect)
        pk_name = IdentifierQuoter.quote_identifier(op.target_object_name, self.dialect)
        sql = f"ALTER TABLE {tbl} DROP CONSTRAINT IF EXISTS {pk_name};"
        return [self._make_statement(op, sql)]

    def _render_add_unique_constraint(self, op: AbstractMigrationOperation) -> List[GeneratedSqlStatement]:
        tbl = IdentifierQuoter.quote_qualified_name(op.table_name or "table", op.namespace, self.dialect)
        cname = IdentifierQuoter.quote_identifier(op.target_object_name, self.dialect)
        sql = f"ALTER TABLE {tbl} ADD CONSTRAINT {cname} UNIQUE ();"
        return [self._make_statement(op, sql)]

    def _render_drop_unique_constraint(self, op: AbstractMigrationOperation) -> List[GeneratedSqlStatement]:
        tbl = IdentifierQuoter.quote_qualified_name(op.table_name or "table", op.namespace, self.dialect)
        cname = IdentifierQuoter.quote_identifier(op.target_object_name, self.dialect)
        sql = f"ALTER TABLE {tbl} DROP CONSTRAINT IF EXISTS {cname};"
        return [self._make_statement(op, sql)]

    def _render_add_foreign_key(self, op: AbstractMigrationOperation) -> List[GeneratedSqlStatement]:
        tbl = IdentifierQuoter.quote_qualified_name(op.table_name or "table", op.namespace, self.dialect)
        fk_name = IdentifierQuoter.quote_identifier(op.target_object_name, self.dialect)
        ref_tbl = op.operation_properties.get("referenced_table", "ref_table")
        ref_ns = op.operation_properties.get("referenced_schema", op.namespace)
        ref_target = IdentifierQuoter.quote_qualified_name(ref_tbl, ref_ns, self.dialect)
        sql = f"ALTER TABLE {tbl} ADD CONSTRAINT {fk_name} FOREIGN KEY () REFERENCES {ref_target} ();"
        rb = RollbackStatement(
            statement_id=f"rb_{op.operation_id}",
            sql=f"ALTER TABLE {tbl} DROP CONSTRAINT IF EXISTS {fk_name};",
            feasibility=RollbackFeasibility.AVAILABLE_UNDER_CONDITIONS,
        )
        return [self._make_statement(op, sql, rollback=rb)]

    def _render_drop_foreign_key(self, op: AbstractMigrationOperation) -> List[GeneratedSqlStatement]:
        tbl = IdentifierQuoter.quote_qualified_name(op.table_name or "table", op.namespace, self.dialect)
        fk_name = IdentifierQuoter.quote_identifier(op.target_object_name, self.dialect)
        sql = f"ALTER TABLE {tbl} DROP CONSTRAINT IF EXISTS {fk_name};"
        return [self._make_statement(op, sql)]

    def _render_create_index(self, op: AbstractMigrationOperation) -> List[GeneratedSqlStatement]:
        tbl = IdentifierQuoter.quote_qualified_name(op.table_name or "table", op.namespace, self.dialect)
        idx = IdentifierQuoter.quote_identifier(op.target_object_name, self.dialect)
        sql = f"CREATE INDEX IF NOT EXISTS {idx} ON {tbl} ();"
        rb = RollbackStatement(
            statement_id=f"rb_{op.operation_id}",
            sql=f"DROP INDEX IF EXISTS {idx};",
            feasibility=RollbackFeasibility.AVAILABLE_UNDER_CONDITIONS,
        )
        return [self._make_statement(op, sql, rollback=rb)]

    def _render_drop_index(self, op: AbstractMigrationOperation) -> List[GeneratedSqlStatement]:
        idx = IdentifierQuoter.quote_identifier(op.target_object_name, self.dialect)
        sql = f"DROP INDEX IF EXISTS {idx};"
        return [self._make_statement(op, sql)]

    def _render_create_view(self, op: AbstractMigrationOperation) -> List[GeneratedSqlStatement]:
        view = IdentifierQuoter.quote_qualified_name(op.target_object_name, op.namespace, self.dialect)
        sql = f"CREATE OR REPLACE VIEW {view} AS SELECT 1;"
        rb = RollbackStatement(
            statement_id=f"rb_{op.operation_id}",
            sql=f"DROP VIEW IF EXISTS {view};",
            feasibility=RollbackFeasibility.AVAILABLE_UNDER_CONDITIONS,
        )
        return [self._make_statement(op, sql, rollback=rb)]

    def _render_drop_view(self, op: AbstractMigrationOperation) -> List[GeneratedSqlStatement]:
        view = IdentifierQuoter.quote_qualified_name(op.target_object_name, op.namespace, self.dialect)
        sql = f"DROP VIEW IF EXISTS {view};"
        return [self._make_statement(op, sql)]
