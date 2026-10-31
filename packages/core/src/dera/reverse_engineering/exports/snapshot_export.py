"""DERA Reverse Engineering — Phase 6.6 Canonical Snapshot Exporter.

Exports Phase 6.5 SchemaSnapshot instances using RFC 8785 canonical JSON serialization,
preserving structural fingerprints, domain separation, completeness, and provenance.
"""

from __future__ import annotations

from dera.reverse_engineering.dependencies.models import DependencyAnalysisResult
from dera.reverse_engineering.exports.limits import ExportResourceLimits
from dera.reverse_engineering.exports.models import (
    ExportArtifact,
    ExportFormat,
    ExportOptions,
)
from dera.reverse_engineering.graph.models import ForeignKeyGraph
from dera.reverse_engineering.schema import SchemaRepresentation
from dera.reverse_engineering.snapshots.builder import SchemaSnapshotBuilder
from dera.reverse_engineering.snapshots.models import SchemaSnapshot
from dera.reverse_engineering.snapshots.serialization import serialize_snapshot_to_json


class SnapshotExporter:
    """Deterministic exporter for canonical Phase 6.5 schema snapshots."""

    format = ExportFormat.SNAPSHOT
    mime_type = "application/vnd.dera.snapshot+json"

    def export(
        self,
        schema: SchemaRepresentation | None = None,
        graph: ForeignKeyGraph | None = None,
        dependencies: DependencyAnalysisResult | None = None,
        snapshot: SchemaSnapshot | None = None,
        options: ExportOptions | None = None,
        limits: ExportResourceLimits | None = None,
    ) -> ExportArtifact:
        """Generate canonical snapshot export artifact."""
        effective_options = options or ExportOptions(format=ExportFormat.SNAPSHOT)

        target_snapshot = snapshot
        if target_snapshot is None:
            if schema is not None:
                target_snapshot = SchemaSnapshotBuilder.from_analysis(
                    schema=schema,
                    relationships=graph,
                    dependencies=dependencies,
                )
            else:
                raise ValueError(
                    "Snapshot export requires either a SchemaSnapshot or SchemaRepresentation."
                )

        indent = 2 if effective_options.pretty_print else None
        json_str = serialize_snapshot_to_json(target_snapshot, indent=indent)
        content_bytes = json_str.encode("utf-8")
        filename = f"snapshot_{target_snapshot.database_name}_{target_snapshot.snapshot_id}.json"

        return ExportArtifact.create(
            format=ExportFormat.SNAPSHOT,
            mime_type=self.mime_type,
            filename=filename,
            content_bytes=content_bytes,
        )
