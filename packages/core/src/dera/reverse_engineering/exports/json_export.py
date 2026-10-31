"""DERA Reverse Engineering — Phase 6.6 Deterministic JSON Exporter.

Serializes canonical schemas, relationship graphs, dependency reports, and snapshots
to deterministic UTF-8 JSON bytes with stable key ordering and explicit nulls.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from dera.reverse_engineering.dependencies.models import DependencyAnalysisResult
from dera.reverse_engineering.exports.limits import ExportResourceLimits
from dera.reverse_engineering.exports.models import (
    ExportArtifact,
    ExportFormat,
    ExportOptions,
    ExportScope,
)
from dera.reverse_engineering.graph.models import ForeignKeyGraph
from dera.reverse_engineering.schema import SchemaRepresentation
from dera.reverse_engineering.snapshots.models import SchemaSnapshot


def _json_default(obj: Any) -> Any:
    """Format non-standard types deterministically."""
    if isinstance(obj, datetime):
        utc_dt = obj if obj.tzinfo is not None else obj.replace(tzinfo=UTC)
        return utc_dt.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    if hasattr(obj, "model_dump"):
        return obj.model_dump(mode="json")
    if hasattr(obj, "value"):
        return obj.value
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


class JSONExporter:
    """Deterministic JSON exporter for reverse engineering models."""

    format = ExportFormat.JSON
    mime_type = "application/json"

    def export(
        self,
        schema: SchemaRepresentation | None = None,
        graph: ForeignKeyGraph | None = None,
        dependencies: DependencyAnalysisResult | None = None,
        snapshot: SchemaSnapshot | None = None,
        options: ExportOptions | None = None,
        limits: ExportResourceLimits | None = None,
    ) -> ExportArtifact:
        """Generate deterministic JSON export artifact based on scope."""
        effective_options = options or ExportOptions(format=ExportFormat.JSON)
        scope = effective_options.scope

        data: dict[str, Any] = {
            "export_version": "dera.export.v1",
            "format": "json",
            "scope": scope.value,
        }

        filename_base = "export"
        if snapshot is not None and scope == ExportScope.SNAPSHOT:
            data["snapshot"] = snapshot.model_dump(mode="json")
            filename_base = f"snapshot_{snapshot.database_name}"
        elif dependencies is not None and scope == ExportScope.DEPENDENCIES:
            data["dependencies"] = dependencies.model_dump(mode="json")
            filename_base = f"dependencies_{dependencies.database_name}"
        elif graph is not None and scope == ExportScope.RELATIONSHIPS:
            data["graph"] = graph.model_dump(mode="json")
            filename_base = f"relationships_{graph.database_name}"
        elif schema is not None:
            filename_base = f"schema_{schema.database.name}"
            if scope == ExportScope.TABLE and effective_options.target_id:
                table = schema.get_table(effective_options.target_id)
                data["table"] = table.model_dump(mode="json") if table else None
                filename_base = f"table_{table.name if table else 'unknown'}"
            elif scope == ExportScope.NAMESPACE and effective_options.target_id:
                tables = [
                    t.model_dump(mode="json")
                    for t in schema.tables
                    if getattr(t, "schema_name", getattr(t, "namespace", ""))
                    == effective_options.target_id
                ]
                data["namespace"] = effective_options.target_id
                data["tables"] = tables
                filename_base = f"namespace_{effective_options.target_id}"
            else:
                data["schema"] = schema.model_dump(mode="json")
        else:
            raise ValueError("No input models provided for JSON export.")

        separators = (",", ": ") if effective_options.pretty_print else (",", ":")
        indent = 2 if effective_options.pretty_print else None

        json_str = json.dumps(
            data,
            indent=indent,
            separators=separators,
            sort_keys=True,
            ensure_ascii=False,
            default=_json_default,
        )
        content_bytes = json_str.encode("utf-8")
        filename = f"{filename_base}.json"

        return ExportArtifact.create(
            format=ExportFormat.JSON,
            mime_type=self.mime_type,
            filename=filename,
            content_bytes=content_bytes,
        )
