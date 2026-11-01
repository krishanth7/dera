"""SQL Artifact Validation Engine.

Performs offline structural and dialect validation on generated SQL statements
without executing them against live customer databases.
"""

from pydantic import BaseModel

from dera.migration.sql.enums import SqlDialectType
from dera.migration.sql.models import GeneratedSqlStatement


class ValidationIssue(BaseModel):
    """Validation finding for a rendered SQL statement."""

    statement_id: str
    issue_type: str
    description: str
    severity: str = "ERROR"


class SqlValidator:
    """Offline structural and syntax validator for migration SQL."""

    @classmethod
    def validate_statements(
        cls,
        statements: list[GeneratedSqlStatement],
        dialect: SqlDialectType,
    ) -> tuple[bool, list[ValidationIssue]]:
        """Validate generated statements structurally."""
        issues: list[ValidationIssue] = []

        for stmt in statements:
            sql = stmt.sql.strip()

            # Rule 1: Must terminate with semicolon
            if not sql.endswith(";"):
                issues.append(
                    ValidationIssue(
                        statement_id=stmt.statement_id,
                        issue_type="TERMINATION_ERROR",
                        description=f"Statement does not terminate with semicolon: {sql[:50]}...",
                    )
                )

            # Rule 2: Unmatched quotation check
            if dialect in (
                SqlDialectType.POSTGRESQL,
                SqlDialectType.SUPABASE,
                SqlDialectType.SQLITE,
            ):
                # Count unescaped double quotes
                # Even count of quotes is required for proper escaping
                quote_count = sql.count('"')
                if quote_count % 2 != 0:
                    issues.append(
                        ValidationIssue(
                            statement_id=stmt.statement_id,
                            issue_type="UNBALANCED_QUOTES",
                            description="Unbalanced double quotes detected in statement.",
                        )
                    )
            elif dialect in (SqlDialectType.MYSQL, SqlDialectType.MARIADB):
                quote_count = sql.count("`")
                if quote_count % 2 != 0:
                    issues.append(
                        ValidationIssue(
                            statement_id=stmt.statement_id,
                            issue_type="UNBALANCED_BACKTICKS",
                            description="Unbalanced backtick quotes detected in statement.",
                        )
                    )

            # Rule 3: No raw injection tokens (e.g. -- or /* injected inside identifiers)
            if "\x00" in sql:
                issues.append(
                    ValidationIssue(
                        statement_id=stmt.statement_id,
                        issue_type="MALICIOUS_TOKEN",
                        description="Null byte detected in statement.",
                        severity="CRITICAL",
                    )
                )

        is_valid = len(issues) == 0
        return is_valid, issues
