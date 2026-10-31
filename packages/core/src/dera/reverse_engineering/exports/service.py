"""DERA Reverse Engineering — Phase 6.6 Export Service.

Orchestrates export generation, validation, circuit breakers, and resource limit enforcement.
"""

from __future__ import annotations

import time

from dera.reverse_engineering.dependencies.models import DependencyAnalysisResult
from dera.reverse_engineering.exports.csv_export import CSVExporter
from dera.reverse_engineering.exports.dot_export import DOTExporter
from dera.reverse_engineering.exports.errors import ExportResourceLimitError
from dera.reverse_engineering.exports.graphml_export import GraphMLExporter
from dera.reverse_engineering.exports.json_export import JSONExporter
from dera.reverse_engineering.exports.limits import ExportResourceLimits
from dera.reverse_engineering.exports.models import (
    ExportArtifact,
    ExportOptions,
)
from dera.reverse_engineering.exports.registry import ExportRegistry
from dera.reverse_engineering.exports.snapshot_export import SnapshotExporter
from dera.reverse_engineering.exports.validation import validate_export_options
from dera.reverse_engineering.graph.models import ForeignKeyGraph
from dera.reverse_engineering.schema import SchemaRepresentation
from dera.reverse_engineering.snapshots.models import SchemaSnapshot


def create_default_export_registry() -> ExportRegistry:
    """Instantiate and populate the default ExportRegistry with standard format exporters."""
    registry = ExportRegistry()
    registry.register(JSONExporter())
    registry.register(CSVExporter())
    registry.register(GraphMLExporter())
    registry.register(DOTExporter())
    registry.register(SnapshotExporter())
    return registry


class ExportService:
    """Public orchestration service for generating reverse engineering export artifacts."""

    def __init__(
        self,
        registry: ExportRegistry | None = None,
        limits: ExportResourceLimits | None = None,
    ) -> None:
        self.registry = registry or create_default_export_registry()
        self.limits = limits or ExportResourceLimits()

    def generate_export(
        self,
        options: ExportOptions,
        schema: SchemaRepresentation | None = None,
        graph: ForeignKeyGraph | None = None,
        dependencies: DependencyAnalysisResult | None = None,
        snapshot: SchemaSnapshot | None = None,
    ) -> ExportArtifact:
        """Validate options, execute format exporter, and enforce payload size limits."""
        # 1. Validate request
        validate_export_options(options, schema=schema, limits=self.limits)

        # 2. Lookup exporter
        exporter = self.registry.get(options.format)

        # 3. Generate export artifact
        t0 = time.perf_counter()
        artifact = exporter.export(
            schema=schema,
            graph=graph,
            dependencies=dependencies,
            snapshot=snapshot,
            options=options,
            limits=self.limits,
        )
        duration = time.perf_counter() - t0

        if duration > self.limits.max_execution_duration_seconds:
            raise ExportResourceLimitError(
                f"Export execution ({duration:.2f}s) exceeded time limit of "
                f"{self.limits.max_execution_duration_seconds}s."
            )

        # 4. Enforce size limit
        if artifact.size_bytes > self.limits.max_export_bytes:
            raise ExportResourceLimitError(
                f"Generated artifact size ({artifact.size_bytes} bytes) exceeds limit of "
                f"{self.limits.max_export_bytes} bytes."
            )

        return artifact
