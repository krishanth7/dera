"""DERA Reverse Engineering — Phase 6.6 Deterministic GraphML Exporter.

Serializes foreign key relationship graphs to standard, valid GraphML (XML)
with strict entity escaping, deterministic node/edge ordering, and composite column metadata.
"""

from __future__ import annotations

import io
from xml.sax.saxutils import escape

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
from dera.reverse_engineering.models import SchemaRepresentation
from dera.reverse_engineering.snapshots.models import SchemaSnapshot


def _xml_attr(val: str | None) -> str:
    """Safely escape XML attribute and text content."""
    if val is None:
        return ""
    return escape(str(val), entities={'"': "&quot;", "'": "&apos;"})


class GraphMLExporter:
    """Deterministic GraphML XML exporter for foreign key relationship graphs."""

    format = ExportFormat.GRAPHML
    mime_type = "application/graphml+xml"

    def export(
        self,
        schema: SchemaRepresentation | None = None,
        graph: ForeignKeyGraph | None = None,
        dependencies: DependencyAnalysisResult | None = None,
        snapshot: SchemaSnapshot | None = None,
        options: ExportOptions | None = None,
        limits: ExportResourceLimits | None = None,
    ) -> ExportArtifact:
        """Generate deterministic GraphML XML artifact."""
        _effective_options = options or ExportOptions(format=ExportFormat.GRAPHML)

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
                    "GraphML export requires either a ForeignKeyGraph or SchemaRepresentation."
                )
        else:
            db_name = target_graph.database_name

        out = io.StringIO()
        out.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        out.write('<graphml xmlns="http://graphml.graphdrawing.org/xmlns"\n')
        out.write('         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n')
        out.write('         xsi:schemaLocation="http://graphml.graphdrawing.org/xmlns\n')
        out.write('         http://graphml.graphdrawing.org/xmlns/1.0/graphml.xsd">\n')

        # Keys
        out.write('  <key id="d_name" for="node" attr.name="name" attr.type="string"/>\n')
        out.write('  <key id="d_namespace" for="node" attr.name="namespace" attr.type="string"/>\n')
        out.write(
            '  <key id="d_constraint" for="edge" attr.name="constraint_name" attr.type="string"/>\n'
        )
        out.write(
            '  <key id="d_source_cols" for="edge" attr.name="source_columns" attr.type="string"/>\n'
        )
        out.write(
            '  <key id="d_target_cols" for="edge" attr.name="target_columns" attr.type="string"/>\n'
        )

        out.write(f'  <graph id="{_xml_attr(db_name)}" edgedefault="directed">\n')

        # Nodes
        sorted_nodes = sort_export_nodes(list(target_graph.nodes.values()))
        for node in sorted_nodes:
            out.write(f'    <node id="{_xml_attr(node.table_id)}">\n')
            out.write(f'      <data key="d_name">{_xml_attr(node.name)}</data>\n')
            out.write(f'      <data key="d_namespace">{_xml_attr(node.namespace)}</data>\n')
            out.write("    </node>\n")

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

            out.write(
                f'    <edge id="{_xml_attr(edge.edge_id)}" source="{_xml_attr(edge.source_table_id)}" target="{_xml_attr(ref_tid)}">\n'
            )
            out.write(f'      <data key="d_constraint">{_xml_attr(edge.native_name)}</data>\n')
            out.write(f'      <data key="d_source_cols">{_xml_attr(src_cols)}</data>\n')
            out.write(f'      <data key="d_target_cols">{_xml_attr(tgt_cols)}</data>\n')
            out.write("    </edge>\n")

        out.write("  </graph>\n")
        out.write("</graphml>\n")

        content_bytes = out.getvalue().encode("utf-8")
        filename = f"graph_{db_name}.graphml"

        return ExportArtifact.create(
            format=ExportFormat.GRAPHML,
            mime_type=self.mime_type,
            filename=filename,
            content_bytes=content_bytes,
        )
