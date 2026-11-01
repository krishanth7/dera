"""Dialect-Aware Safe Identifier Quoting and Sanitization.

Enforces strict SQL injection prevention, reserved keyword handling,
and proper dialect-specific quoting without vulnerable string interpolations.
"""

from dera.migration.sql.enums import SqlDialectType


class IdentifierQuoter:
    """Deterministic dialect-aware identifier escaping."""

    @classmethod
    def quote_identifier(cls, identifier: str, dialect: SqlDialectType) -> str:
        """Escape and quote an individual identifier according to dialect rules."""
        if not identifier:
            raise ValueError("Identifier cannot be empty or None.")

        # Reject null bytes or dangerous control characters
        if "\x00" in identifier:
            raise ValueError(f"Malicious identifier with null byte detected: {repr(identifier)}")

        if dialect in (SqlDialectType.POSTGRESQL, SqlDialectType.SUPABASE, SqlDialectType.SQLITE):
            # Double quotes: double any embedded double quotes
            escaped = identifier.replace('"', '""')
            return f'"{escaped}"'

        elif dialect in (SqlDialectType.MYSQL, SqlDialectType.MARIADB):
            # Backticks: double any embedded backticks
            escaped = identifier.replace("`", "``")
            return f"`{escaped}`"

        raise ValueError(f"Unsupported SQL dialect for identifier quoting: {dialect}")

    @classmethod
    def quote_qualified_name(
        cls,
        name: str,
        namespace: str | None,
        dialect: SqlDialectType,
    ) -> str:
        """Quote a schema-qualified object name (e.g. "public"."users" or `mydb`.`users`)."""
        quoted_name = cls.quote_identifier(name, dialect)
        if not namespace or dialect == SqlDialectType.SQLITE:
            return quoted_name
        quoted_ns = cls.quote_identifier(namespace, dialect)
        return f"{quoted_ns}.{quoted_name}"
