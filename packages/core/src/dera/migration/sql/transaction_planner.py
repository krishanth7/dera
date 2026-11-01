"""Transaction Planner.

Groups generated SQL statements into coherent transaction blocks
respecting dialect-specific transactional DDL capabilities:
- PostgreSQL/Supabase: Groups transactional DDL in BEGIN ... COMMIT.
- SQLite: Groups in BEGIN TRANSACTION ... COMMIT.
- MySQL/MariaDB: Disables multi-statement transaction wrapping due to implicit commits on DDL.
"""

from dera.migration.sql.enums import SqlDialectType, TransactionExecutionMode
from dera.migration.sql.models import GeneratedSqlStatement, TransactionBlock


class TransactionPlanner:
    """Plans and structures transaction boundaries for SQL statements."""

    @classmethod
    def plan_transactions(
        cls,
        statements: list[GeneratedSqlStatement],
        dialect: SqlDialectType,
    ) -> list[TransactionBlock]:
        """Group statements into transaction blocks."""
        if not statements:
            return []

        if dialect in (SqlDialectType.POSTGRESQL, SqlDialectType.SUPABASE):
            # PostgreSQL supports full transactional DDL
            stmt_lines = [s.sql for s in statements]
            block_sql = "BEGIN;\n\n" + "\n".join(stmt_lines) + "\n\nCOMMIT;"
            return [
                TransactionBlock(
                    block_id="tx_block_1",
                    block_order=1,
                    execution_mode=TransactionExecutionMode.TRANSACTIONAL,
                    statement_ids=[s.statement_id for s in statements],
                    rendered_block_sql=block_sql,
                )
            ]

        elif dialect == SqlDialectType.SQLITE:
            stmt_lines = [s.sql for s in statements]
            block_sql = "BEGIN TRANSACTION;\n\n" + "\n".join(stmt_lines) + "\n\nCOMMIT;"
            return [
                TransactionBlock(
                    block_id="tx_block_1",
                    block_order=1,
                    execution_mode=TransactionExecutionMode.TRANSACTIONAL,
                    statement_ids=[s.statement_id for s in statements],
                    rendered_block_sql=block_sql,
                )
            ]

        elif dialect in (SqlDialectType.MYSQL, SqlDialectType.MARIADB):
            # MySQL / MariaDB execute DDL with implicit commits; wrap individually
            blocks = []
            for idx, s in enumerate(statements, start=1):
                blocks.append(
                    TransactionBlock(
                        block_id=f"tx_block_{idx}",
                        block_order=idx,
                        execution_mode=TransactionExecutionMode.IMPLICIT_COMMIT,
                        statement_ids=[s.statement_id],
                        rendered_block_sql=s.sql,
                    )
                )
            return blocks

        return []
