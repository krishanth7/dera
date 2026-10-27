"""DERA Connectors — Metadata Query Allowlist & Policy Registry.

Maintains an immutable registry of approved metadata introspection queries,
parameter specifications, result row limits, and engine compatibility.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from dera_connectors.security.errors import UnauthorizedQueryError
from dera_connectors.security.readonly import validate_read_only_sql


@dataclass(frozen=True)
class QuerySpecification:
    """Specification for an authorized catalog inspection query."""

    operation_id: str
    supported_engines: frozenset[str]
    description: str
    required_capabilities: tuple[str, ...] = ()
    max_result_rows: int = 50_000
    timeout_seconds: float = 30.0
    allowed_parameters: tuple[str, ...] = ()


class ApprovedMetadataQueryRegistry:
    """Central registry of approved database introspection operations."""

    def __init__(self) -> None:
        self._registry: dict[str, QuerySpecification] = {}
        self._register_default_catalog_queries()

    def register(self, spec: QuerySpecification) -> None:
        """Register an authorized query specification."""
        self._registry[spec.operation_id] = spec

    def get(self, operation_id: str) -> QuerySpecification | None:
        """Retrieve specification for an operation ID."""
        return self._registry.get(operation_id)

    def validate_operation(
        self,
        operation_id: str,
        engine: str,
        sql: str,
        parameters: dict[str, Any] | None = None,
    ) -> QuerySpecification:
        """Validate an intended database query against the allowlist policy.

        Parameters
        ----------
        operation_id : str
            Unique operation identifier.
        engine : str
            Target database engine identifier.
        sql : str
            SQL query string to be executed.
        parameters : dict[str, Any] | None
            Query parameters.

        Returns
        -------
        QuerySpecification
            Approved query specification.

        Raises
        ------
        UnauthorizedQueryError
            If operation is unregistered or incompatible with target engine.
        ReadOnlySecurityViolationError
            If query contains prohibited mutation tokens.
        """
        # 1. First enforce strict read-only lexical analysis
        validate_read_only_sql(sql)

        # 2. Check registry
        spec = self.get(operation_id)
        if spec is None:
            raise UnauthorizedQueryError(
                operation_id=operation_id,
                reason=f"Operation ID '{operation_id}' is not in the approved metadata query registry.",
            )

        # 3. Check engine compatibility
        engine_lower = engine.strip().lower()
        if engine_lower not in spec.supported_engines and "any" not in spec.supported_engines:
            raise UnauthorizedQueryError(
                operation_id=operation_id,
                reason=f"Operation '{operation_id}' is not supported for database engine '{engine}'. Supported: {sorted(spec.supported_engines)}",
            )

        # 4. Check parameter keys against allowed parameters
        if parameters and spec.allowed_parameters:
            for param_key in parameters.keys():
                if param_key not in spec.allowed_parameters:
                    raise UnauthorizedQueryError(
                        operation_id=operation_id,
                        reason=f"Unrecognized parameter '{param_key}' for operation '{operation_id}'. Allowed: {spec.allowed_parameters}",
                    )

        return spec

    def _register_default_catalog_queries(self) -> None:
        """Register built-in Phase 5 catalog operations across all supported engines."""
        defaults = [
            # PostgreSQL & Supabase
            QuerySpecification(
                operation_id="postgres.catalog.schemas",
                supported_engines=frozenset({"postgresql", "supabase"}),
                description="Inspect accessible database schemas from pg_namespace",
            ),
            QuerySpecification(
                operation_id="postgres.catalog.tables",
                supported_engines=frozenset({"postgresql", "supabase"}),
                description="Inspect user tables from information_schema.tables and pg_class",
            ),
            QuerySpecification(
                operation_id="postgres.catalog.columns",
                supported_engines=frozenset({"postgresql", "supabase"}),
                description="Inspect table columns from information_schema.columns and pg_attribute",
            ),
            QuerySpecification(
                operation_id="postgres.catalog.constraints",
                supported_engines=frozenset({"postgresql", "supabase"}),
                description="Inspect primary, foreign key, unique, and check constraints",
            ),
            QuerySpecification(
                operation_id="postgres.catalog.indexes",
                supported_engines=frozenset({"postgresql", "supabase"}),
                description="Inspect index terms and expressions from pg_index and pg_class",
            ),
            QuerySpecification(
                operation_id="postgres.catalog.views",
                supported_engines=frozenset({"postgresql", "supabase"}),
                description="Inspect view definitions from information_schema.views",
            ),
            QuerySpecification(
                operation_id="postgres.catalog.triggers",
                supported_engines=frozenset({"postgresql", "supabase"}),
                description="Inspect trigger metadata from information_schema.triggers",
            ),
            # SQLite
            QuerySpecification(
                operation_id="sqlite.catalog.tables",
                supported_engines=frozenset({"sqlite"}),
                description="Inspect tables and views from sqlite_master",
            ),
            QuerySpecification(
                operation_id="sqlite.catalog.columns",
                supported_engines=frozenset({"sqlite"}),
                description="Inspect column definitions via PRAGMA table_xinfo / table_info",
            ),
            QuerySpecification(
                operation_id="sqlite.catalog.foreign_keys",
                supported_engines=frozenset({"sqlite"}),
                description="Inspect foreign keys via PRAGMA foreign_key_list",
            ),
            QuerySpecification(
                operation_id="sqlite.catalog.indexes",
                supported_engines=frozenset({"sqlite"}),
                description="Inspect indexes via PRAGMA index_list and index_xinfo",
            ),
            # MySQL & MariaDB
            QuerySpecification(
                operation_id="mysql.catalog.tables",
                supported_engines=frozenset({"mysql", "mariadb"}),
                description="Inspect database tables from information_schema.tables",
            ),
            QuerySpecification(
                operation_id="mysql.catalog.columns",
                supported_engines=frozenset({"mysql", "mariadb"}),
                description="Inspect table columns from information_schema.columns",
            ),
            QuerySpecification(
                operation_id="mysql.catalog.constraints",
                supported_engines=frozenset({"mysql", "mariadb"}),
                description="Inspect primary, foreign key, and unique constraints from table_constraints",
            ),
            QuerySpecification(
                operation_id="mysql.catalog.check_constraints",
                supported_engines=frozenset({"mysql", "mariadb"}),
                description="Inspect check constraints from information_schema.check_constraints",
            ),
            QuerySpecification(
                operation_id="mysql.catalog.indexes",
                supported_engines=frozenset({"mysql", "mariadb"}),
                description="Inspect index metadata from information_schema.statistics",
            ),
            QuerySpecification(
                operation_id="mysql.catalog.views",
                supported_engines=frozenset({"mysql", "mariadb"}),
                description="Inspect view definitions from information_schema.views",
            ),
            QuerySpecification(
                operation_id="mysql.catalog.triggers",
                supported_engines=frozenset({"mysql", "mariadb"}),
                description="Inspect triggers from information_schema.triggers",
            ),
        ]
        for spec in defaults:
            self.register(spec)


# Global default query registry instance
GLOBAL_QUERY_REGISTRY = ApprovedMetadataQueryRegistry()
