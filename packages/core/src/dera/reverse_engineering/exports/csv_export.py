"""DERA Reverse Engineering — Phase 6.6 Safe CSV Exporter.

Serializes database schemas, columns, relationships, and dependencies to CSV format
with built-in spreadsheet formula injection defense (safe mode).
"""

from __future__ import annotations

import csv
import io

from dera.reverse_engineering.dependencies.models import DependencyAnalysisResult
from dera.reverse_engineering.exports.limits import ExportResourceLimits
from dera.reverse_engineering.exports.models import (
    ExportArtifact,
    ExportFormat,
    ExportOptions,
    ExportScope,
)
from dera.reverse_engineering.exports.ordering import (
    sort_export_columns,
    sort_export_edges,
    sort_export_tables,
)
from dera.reverse_engineering.graph.models import ForeignKeyGraph
from dera.reverse_engineering.models import SchemaRepresentation
from dera.reverse_engineering.snapshots.models import SchemaSnapshot

_DANGEROUS_FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def sanitize_csv_cell(value: str | None, safe_mode: bool = True) -> str:
    """Sanitize CSV cell content against spreadsheet formula injection (CSV Injection).

    If safe_mode is True, values whose stripped prefix matches dangerous formula characters
    (=, +, -, @, \\t, \\r) are prepended with an apostrophe (').
    """
    if value is None:
        return ""
    str_val = str(value)
    if not safe_mode:
        return str_val

    stripped = str_val.lstrip()
    if stripped.startswith(_DANGEROUS_FORMULA_PREFIXES):
        return f"'{str_val}"
    return str_val


class CSVExporter:
    """Deterministic CSV exporter with formula injection defense."""

    format = ExportFormat.CSV
    mime_type = "text/csv; charset=utf-8"

    def export(
        self,
        schema: SchemaRepresentation | None = None,
        graph: ForeignKeyGraph | None = None,
        dependencies: DependencyAnalysisResult | None = None,
        snapshot: SchemaSnapshot | None = None,
        options: ExportOptions | None = None,
        limits: ExportResourceLimits | None = None,
    ) -> ExportArtifact:
        """Generate deterministic CSV export artifact based on scope."""
        effective_options = options or ExportOptions(format=ExportFormat.CSV)
        safe = effective_options.safe_mode
        scope = effective_options.scope

        output = io.StringIO()
        writer = csv.writer(output, lineterminator="\n")

        filename_base = "export"

        if scope == ExportScope.RELATIONSHIPS and graph is not None:
            filename_base = f"relationships_{graph.database_name}"
            writer.writerow(
                [
                    "edge_id",
                    "source_table_id",
                    "source_table_name",
                    "target_table_id",
                    "target_table_name",
                    "constraint_name",
                    "source_columns",
                    "target_columns",
                    "on_delete",
                    "on_update",
                ]
            )
            sorted_edges = sort_export_edges(list(graph.edges))
            for edge in sorted_edges:
                writer.writerow(
                    [
                        sanitize_csv_cell(edge.edge_id, safe),
                        sanitize_csv_cell(edge.source_table_id, safe),
                        sanitize_csv_cell(edge.source_table_name, safe),
                        sanitize_csv_cell(
                            getattr(
                                edge, "referenced_table_id", getattr(edge, "target_table_id", "")
                            ),
                            safe,
                        ),
                        sanitize_csv_cell(
                            getattr(
                                edge,
                                "referenced_table_name",
                                getattr(edge, "target_table_name", ""),
                            ),
                            safe,
                        ),
                        sanitize_csv_cell(edge.native_name, safe),
                        sanitize_csv_cell(
                            ",".join(
                                getattr(
                                    edge, "source_column_names", getattr(edge, "source_columns", ())
                                )
                            ),
                            safe,
                        ),
                        sanitize_csv_cell(
                            ",".join(
                                getattr(
                                    edge,
                                    "referenced_column_names",
                                    getattr(edge, "target_columns", ()),
                                )
                            ),
                            safe,
                        ),
                        sanitize_csv_cell(str(edge.on_delete), safe),
                        sanitize_csv_cell(str(edge.on_update), safe),
                    ]
                )

        elif scope == ExportScope.DEPENDENCIES and dependencies is not None:
            filename_base = f"dependencies_{dependencies.database_name}"
            writer.writerow(
                [
                    "table_id",
                    "topological_level",
                    "in_cycle",
                    "scc_id",
                ]
            )
            # Write ordered levels
            table_to_level: dict[str, int] = {}
            for lvl in dependencies.ordering.levels:
                for tid in lvl.table_ids:
                    table_to_level[tid] = lvl.level_index

            scc_map: dict[str, str] = {}
            for scc in dependencies.cycle_report.components:
                for tid in scc.table_ids:
                    scc_map[tid] = scc.scc_id

            sorted_tids = sorted(table_to_level.keys())
            for tid in sorted_tids:
                in_cycle = tid in scc_map
                writer.writerow(
                    [
                        sanitize_csv_cell(tid, safe),
                        str(table_to_level.get(tid, -1)),
                        str(in_cycle),
                        sanitize_csv_cell(scc_map.get(tid, ""), safe),
                    ]
                )

        elif schema is not None:
            filename_base = f"schema_{schema.database.name}"
            writer.writerow(
                [
                    "namespace",
                    "table_name",
                    "ordinal_position",
                    "column_name",
                    "native_type",
                    "canonical_type",
                    "is_nullable",
                    "is_primary_key",
                    "default_expression",
                ]
            )

            tables = list(schema.tables)
            if scope == ExportScope.TABLE and effective_options.target_id:
                t = schema.get_table(effective_options.target_id)
                tables = [t] if t else []
                filename_base = f"table_{t.name if t else 'unknown'}"
            elif scope == ExportScope.NAMESPACE and effective_options.target_id:
                tables = [
                    t
                    for t in tables
                    if getattr(t, "schema_name", getattr(t, "namespace", ""))
                    == effective_options.target_id
                ]
                filename_base = f"namespace_{effective_options.target_id}"

            sorted_tables = sort_export_tables(tables)
            for tbl in sorted_tables:
                ns = getattr(tbl, "schema_name", getattr(tbl, "namespace", "public"))
                pk_cols = set(tbl.primary_key.column_names) if tbl.primary_key else set()

                sorted_cols = sort_export_columns(list(tbl.columns))
                for col in sorted_cols:
                    is_pk = col.name in pk_cols
                    writer.writerow(
                        [
                            sanitize_csv_cell(ns, safe),
                            sanitize_csv_cell(tbl.name, safe),
                            str(col.ordinal_position),
                            sanitize_csv_cell(col.name, safe),
                            sanitize_csv_cell(
                                getattr(col, "native_data_type", getattr(col, "native_type", "")),
                                safe,
                            ),
                            sanitize_csv_cell(str(col.canonical_type), safe),
                            str(col.is_nullable),
                            str(is_pk),
                            sanitize_csv_cell(getattr(col, "default_expression", None), safe),
                        ]
                    )
        else:
            raise ValueError("No input models provided for CSV export.")

        csv_content = output.getvalue()
        content_bytes = csv_content.encode("utf-8")
        filename = f"{filename_base}.csv"

        return ExportArtifact.create(
            format=ExportFormat.CSV,
            mime_type=self.mime_type,
            filename=filename,
            content_bytes=content_bytes,
        )
