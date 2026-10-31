"""DERA Reverse Engineering — Phase 6.6 Export Registry.

Centralized registry for format-specific exporters. Enforces typed dispatch
and rejects unsupported export formats.
"""

from __future__ import annotations

from typing import Protocol

from dera.reverse_engineering.dependencies.models import DependencyAnalysisResult
from dera.reverse_engineering.exports.errors import UnsupportedExportFormatError
from dera.reverse_engineering.exports.limits import ExportResourceLimits
from dera.reverse_engineering.exports.models import (
    ExportArtifact,
    ExportFormat,
    ExportOptions,
)
from dera.reverse_engineering.graph.models import ForeignKeyGraph
from dera.reverse_engineering.models import SchemaRepresentation
from dera.reverse_engineering.snapshots.models import SchemaSnapshot


class ExporterProtocol(Protocol):
    """Protocol implemented by all format-specific exporters."""

    format: ExportFormat
    mime_type: str

    def export(
        self,
        schema: SchemaRepresentation | None = None,
        graph: ForeignKeyGraph | None = None,
        dependencies: DependencyAnalysisResult | None = None,
        snapshot: SchemaSnapshot | None = None,
        options: ExportOptions | None = None,
        limits: ExportResourceLimits | None = None,
    ) -> ExportArtifact: ...


class ExportRegistry:
    """Registry maintaining active exporter instances."""

    def __init__(self) -> None:
        self._exporters: dict[ExportFormat, ExporterProtocol] = {}

    def register(self, exporter: ExporterProtocol) -> None:
        """Register an exporter for its declared ExportFormat."""
        self._exporters[exporter.format] = exporter

    def get(self, format_type: ExportFormat | str) -> ExporterProtocol:
        """Retrieve an exporter by format or raise UnsupportedExportFormatError."""
        try:
            fmt = ExportFormat(format_type) if isinstance(format_type, str) else format_type
        except ValueError as exc:
            raise UnsupportedExportFormatError(f"Unsupported export format: {format_type}") from exc

        exporter = self._exporters.get(fmt)
        if exporter is None:
            raise UnsupportedExportFormatError(f"No exporter registered for format: {fmt.value}")
        return exporter

    def supported_formats(self) -> list[ExportFormat]:
        """Return list of registered export formats."""
        return list(self._exporters.keys())
