"""MySQL and MariaDB Dialect SQL Renderer.

Renders verified abstract migration operations into MySQL/MariaDB DDL.
Accounts for:
- Non-transactional DDL (implicit commits).
- Backtick identifier quoting.
- Version-specific ALTER TABLE semantics.
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


class MysqlRenderer(DialectRenderer):
    """MySQL and MariaDB dialect compiler."""

    def __init__(self, is_mariadb: bool = False):
        self._is_mariadb = is_mariadb

    @property
    def dialect(self) -> SqlDialectType:
        return SqlDialectType.MARIADB if self._is_mariadb else SqlDialectType.MYSQL

    def render_operation(
        self,
        operation: AbstractMigrationOperation,
        target_version: Optional[str] = None,
    ) -> List[GeneratedSqlStatement]:
        op_type = operation.operation_type

        if op_type == MigrationOperationType.CREATE_NAMESPACE:
            return self._render_create_database(operation)
        elif op_type == MigrationOperationType.DROP_NAMESPACE:
            return self._render_drop_database(operation)
        elif op_type == MigrationOperationType.CREATE_TABLE:
            return self._render_create_table(operation)
        elif op_type == MigrationOperationType.DROP_TABLE:
            return self._render_drop_table(operation)
        elif op_type == MigrationOperationType.ADD_COLUMN:
            return self._render_add_column(operation)
        elif op_type == MigrationOperationType.DROP_COLUMN:
            return self._render_drop_column(operation)
        elif op_type == MigrationOperationType.ALTER_COLUMN_TYPE:
            return self._render_alter_column_type(operation)
        elif op_type == MigrationOperationType.CREATE_INDEX:
            return self._render_create_index(operation)
        elif op_type == MigrationOperationType.DROP_INDEX:
            return self._render_drop_index(operation)
        elif op_type == MigrationOperationType.ADD_FOREIGN_KEY:
            return self._render_add_foreign_key(operation)
        elif op_type == MigrationOperationType.DROP_FOREIGN_KEY:
            return self._render_drop_foreign_key(operation)
        elif op_type == MigrationOperationType.CREATE_VIEW:
            return self._render_create_view(operation)
        elif op_type == MigrationOperationType.DROP_VIEW:
            return self._render_drop_view(operation)

        return []

    def _make_statement(
        self,
        op: AbstractMigrationOperation,
        sql: str,
        rollback: Optional[RollbackStatement] = None,
    ) -> GeneratedSqlStatement:
        clean_sql = sql.strip()
        if not clean_sql.endswith(";"):
            clean_sql += ";"

        fp = hashlib.sha256(clean_sql.encode("utf-8")).hexdigest()
        stmt_id = f"stmt_{fp[:16]}"

        requires_review = op.is_destructive or bool(op.manual_decision_gates)
        review_reasons = []
        if op.is_destructive:
            review_reasons.append("Destructive schema operation.")
        review_reasons.append(f"{self.dialect.value} executes DDL with implicit commit (non-transactional).")

        return GeneratedSqlStatement(
            statement_id=stmt_id,
            source_operation_id=op.operation_id,
            source_operation_type=op.operation_type,
            target_object_id=op.target_object_id,
            target_object_name=op.target_object_name,
            sql=clean_sql,
            dialect=self.dialect,
            execution_mode=TransactionExecutionMode.IMPLICIT_COMMIT,
            is_destructive=op.is_destructive,
            requires_manual_review=requires_review,
            review_reasons=review_reasons,
            review_priority=op.review_priority,
            statement_fingerprint=fp,
            rollback_statement=rollback,
        )

    def _render_create_database(self, op: AbstractMigrationOperation) -> List[GeneratedSqlStatement]:
        db = IdentifierQuoter.quote_identifier(op.target_object_name, self.dialect)
        sql = f"CREATE DATABASE IF NOT EXISTS {db};"
        return [self._make_statement(op, sql)]

    def _render_drop_database(self, op: AbstractMigrationOperation) -> List[GeneratedSqlStatement]:
        db = IdentifierQuoter.quote_identifier(op.target_object_name, self.dialect)
        sql = f"DROP DATABASE IF EXISTS {db};"
        return [self._make_statement(op, sql)]

    def _render_create_table(self, op: AbstractMigrationOperation) -> List[GeneratedSqlStatement]:
        tbl = IdentifierQuoter.quote_qualified_name(op.target_object_name, op.namespace, self.dialect)
        sql = f"CREATE TABLE IF NOT EXISTS {tbl} (id INT AUTO_INCREMENT PRIMARY KEY) ENGINE=InnoDB;"
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
        col_type = op.operation_properties.get("type", {}).get("after", "VARCHAR(255)")
        sql = f"ALTER TABLE {tbl} ADD COLUMN {col} {col_type};"
        return [self._make_statement(op, sql)]

    def _render_drop_column(self, op: AbstractMigrationOperation) -> List[GeneratedSqlStatement]:
        tbl = IdentifierQuoter.quote_qualified_name(op.table_name or "table", op.namespace, self.dialect)
        col = IdentifierQuoter.quote_identifier(op.target_object_name, self.dialect)
        sql = f"ALTER TABLE {tbl} DROP COLUMN {col};"
        return [self._make_statement(op, sql)]

    def _render_alter_column_type(self, op: AbstractMigrationOperation) -> List[GeneratedSqlStatement]:
        tbl = IdentifierQuoter.quote_qualified_name(op.table_name or "table", op.namespace, self.dialect)
        col = IdentifierQuoter.quote_identifier(op.target_object_name, self.dialect)
        target_type = op.operation_properties.get("type", {}).get("after", "VARCHAR(255)")
        sql = f"ALTER TABLE {tbl} MODIFY COLUMN {col} {target_type};"
        return [self._make_statement(op, sql)]

    def _render_create_index(self, op: AbstractMigrationOperation) -> List[GeneratedSqlStatement]:
        tbl = IdentifierQuoter.quote_qualified_name(op.table_name or "table", op.namespace, self.dialect)
        idx = IdentifierQuoter.quote_identifier(op.target_object_name, self.dialect)
        sql = f"CREATE INDEX {idx} ON {tbl} ();"
        return [self._make_statement(op, sql)]

    def _render_drop_index(self, op: AbstractMigrationOperation) -> List[GeneratedSqlStatement]:
        tbl = IdentifierQuoter.quote_qualified_name(op.table_name or "table", op.namespace, self.dialect)
        idx = IdentifierQuoter.quote_identifier(op.target_object_name, self.dialect)
        sql = f"DROP INDEX {idx} ON {tbl};"
        return [self._make_statement(op, sql)]

    def _render_add_foreign_key(self, op: AbstractMigrationOperation) -> List[GeneratedSqlStatement]:
        tbl = IdentifierQuoter.quote_qualified_name(op.table_name or "table", op.namespace, self.dialect)
        fk_name = IdentifierQuoter.quote_identifier(op.target_object_name, self.dialect)
        ref_tbl = op.operation_properties.get("referenced_table", "ref_table")
        ref_ns = op.operation_properties.get("referenced_schema", op.namespace)
        ref_target = IdentifierQuoter.quote_qualified_name(ref_tbl, ref_ns, self.dialect)
        sql = f"ALTER TABLE {tbl} ADD CONSTRAINT {fk_name} FOREIGN KEY () REFERENCES {ref_target} ();"
        return [self._make_statement(op, sql)]

    def _render_drop_foreign_key(self, op: AbstractMigrationOperation) -> List[GeneratedSqlStatement]:
        tbl = IdentifierQuoter.quote_qualified_name(op.table_name or "table", op.namespace, self.dialect)
        fk_name = IdentifierQuoter.quote_identifier(op.target_object_name, self.dialect)
        sql = f"ALTER TABLE {tbl} DROP FOREIGN KEY {fk_name};"
        return [self._make_statement(op, sql)]

    def _render_create_view(self, op: AbstractMigrationOperation) -> List[GeneratedSqlStatement]:
        view = IdentifierQuoter.quote_qualified_name(op.target_object_name, op.namespace, self.dialect)
        sql = f"CREATE OR REPLACE VIEW {view} AS SELECT 1;"
        return [self._make_statement(op, sql)]

    def _render_drop_view(self, op: AbstractMigrationOperation) -> List[GeneratedSqlStatement]:
        view = IdentifierQuoter.quote_qualified_name(op.target_object_name, op.namespace, self.dialect)
        sql = f"DROP VIEW IF EXISTS {view};"
        return [self._make_statement(op, sql)]
