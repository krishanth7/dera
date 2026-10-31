"""DERA Reverse Engineering — Phase 6.6 Deterministic Graphviz DOT Exporter.

Serializes foreign key relationship graphs to Graphviz DOT format with strict string escaping,
preventing DOT statement injection and preserving parallel edges and self-loops.
"""

from __future__ import annotations

import io

from dera.reverse_engineering.dependencies.models import DependencyAnalysisResult
from dera.reverse_engineering.exports.limits import ExportResourceLimits
from dera.reverse_engineering.exports.models import (
    ExportArtifact,
    ExportFormat,
    ExportOptions,
)
from dera.reverse_engineering.exports.ordering import sort_export_edges, sort_export_nodes
from dera.reverse_engineering.graph.builder import ForeignKeyGraphBuilder
from dera.reverse_engineering.graph.models import ForeignKeyGraph
from dera.reverse_engineering.schema import SchemaRepresentation
from dera.reverse_engineering.snapshots.models import SchemaSnapshot


def _dot_escape(s: str | None) -> str:
    """Safely escape strings for Graphviz double-quoted attributes."""
    if s is None:
        return ""
    # Escape backslashes and double quotes
    escaped = str(s).replace("\\", "\\\\").replace('"', '\\"')
    # Prevent newline breakout
    escaped = escaped.replace("\r", "").replace("\n", "\\n")
    return escaped


class DOTExporter:
    """Deterministic Graphviz DOT exporter for relationship graphs."""

    format = ExportFormat.DOT
    mime_type = "text/vnd.graphviz"

    def export(
        self,
        schema: SchemaRepresentation | None = None,
        graph: ForeignKeyGraph | None = None,
        dependencies: DependencyAnalysisResult | None = None,
        snapshot: SchemaSnapshot | None = None,
        options: ExportOptions | None = None,
        limits: ExportResourceLimits | None = None,
    ) -> ExportArtifact:
        """Generate deterministic Graphviz DOT artifact."""
        _effective_options = options or ExportOptions(format=ExportFormat.DOT)

        # Resolve or construct graph
        target_graph = graph
        db_name = "database"
        if target_graph is None:
            if schema is not None:
                db_name = schema.database.name
                builder = ForeignKeyGraphBuilder()
                target_graph = builder.build(schema)
            else:
                raise ValueError(
                    "DOT export requires either a ForeignKeyGraph or SchemaRepresentation."
                )
        else:
            db_name = target_graph.database_name

        out = io.StringIO()
        out.write(f'digraph "{_dot_escape(db_name)}" {{\n')
        out.write("  rankdir=LR;\n")
        out.write(
            '  node [shape=box, style="filled,rounded", fillcolor="#f8fafc", color="#94a3b8", fontname="Helvetica"];\n'
        )
        out.write('  edge [fontname="Helvetica", fontsize=10, color="#64748b"];\n\n')

        # Nodes
        sorted_nodes = sort_export_nodes(list(target_graph.nodes.values()))
        for node in sorted_nodes:
            label = f"{node.namespace}.{node.name}" if node.namespace else node.name
            out.write(f'  "{_dot_escape(node.table_id)}" [label="{_dot_escape(label)}"];\n')

        out.write("\n")

        # Edges
        sorted_edges = sort_export_edges(list(target_graph.edges))
        for edge in sorted_edges:
            ref_tid = getattr(edge, "referenced_table_id", getattr(edge, "target_table_id", ""))
            src_cols = ",".join(
                getattr(edge, "source_column_names", getattr(edge, "source_columns", ()))
            )
            tgt_cols = ",".join(
                getattr(edge, "referenced_column_names", getattr(edge, "target_columns", ()))
            )
            label = f"{edge.native_name} ({src_cols} -> {tgt_cols})"

            out.write(
                f'  "{_dot_escape(edge.source_table_id)}" -> "{_dot_escape(ref_tid)}" [label="{_dot_escape(label)}"];\n'
            )

        out.write("}\n")

        content_bytes = out.getvalue().encode("utf-8")
        filename = f"graph_{db_name}.dot"

        return ExportArtifact.create(
            format=ExportFormat.DOT,
            mime_type=self.mime_type,
            filename=filename,
            content_bytes=content_bytes,
        )
