"""DERA Reverse Engineering — Phase 6.6 Export Validation Engine.

Validates export configuration, requested scopes, target IDs, and resource limits
before computationally intensive export generation begins.
"""

from __future__ import annotations

from dera.reverse_engineering.exports.errors import (
    ExportResourceLimitError,
    ExportValidationError,
    UnsupportedExportFormatError,
)
from dera.reverse_engineering.exports.limits import ExportResourceLimits
from dera.reverse_engineering.exports.models import ExportFormat, ExportOptions, ExportScope
from dera.reverse_engineering.models import SchemaRepresentation


def validate_export_options(
    options: ExportOptions,
    schema: SchemaRepresentation | None = None,
    limits: ExportResourceLimits | None = None,
) -> None:
    """Validate requested export options against available schema data and resource limits."""
    effective_limits = limits or ExportResourceLimits()

    # 1. Format check
    if options.format not in ExportFormat:
        raise UnsupportedExportFormatError(f"Unsupported export format: {options.format}")

    # 2. Scope & Target ID check
    if options.scope == ExportScope.TABLE:
        if not options.target_id:
            raise ExportValidationError("Scope 'table' requires target_id (canonical table ID).")
        if schema is not None:
            table = schema.get_table(options.target_id)
            if not table:
                raise ExportValidationError(
                    f"Table with ID '{options.target_id}' not found in schema."
                )

    elif options.scope == ExportScope.NAMESPACE:
        if not options.target_id:
            raise ExportValidationError(
                "Scope 'namespace' requires target_id (native namespace name)."
            )
        if schema is not None:
            ns_names = {ns.name for ns in schema.namespaces}
            if options.target_id not in ns_names:
                raise ExportValidationError(f"Namespace '{options.target_id}' not found in schema.")

    # 3. Resource boundaries check on schema
    if schema is not None:
        table_count = len(schema.tables)
        if table_count > effective_limits.max_table_count:
            raise ExportResourceLimitError(
                f"Schema table count ({table_count}) exceeds limit of {effective_limits.max_table_count}."
            )
        col_count = sum(len(t.columns) for t in schema.tables)
        if col_count > effective_limits.max_column_count:
            raise ExportResourceLimitError(
                f"Schema column count ({col_count}) exceeds limit of {effective_limits.max_column_count}."
            )
