"""DERA API — Phase 6.6 Reverse Engineering Application Service.

Coordinates schema representations, foreign key graphs, dependency analysis,
schema snapshots, deterministic export generation, and tenant isolation.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from dera.reverse_engineering.dependencies.analyzer import DependencyAnalyzer
from dera.reverse_engineering.dependencies.models import DependencyAnalysisResult
from dera.reverse_engineering.exports.models import (
    ExportArtifact,
    ExportOptions,
)
from dera.reverse_engineering.exports.service import ExportService
from dera.reverse_engineering.graph.builder import ForeignKeyGraphBuilder
from dera.reverse_engineering.graph.models import ForeignKeyGraph
from dera.reverse_engineering.models import SchemaRepresentation
from dera.reverse_engineering.snapshots.builder import SchemaSnapshotBuilder
from dera.reverse_engineering.snapshots.integrity import (
    SnapshotIntegrityReport,
    verify_snapshot_integrity,
)
from dera.reverse_engineering.snapshots.models import SchemaSnapshot
from dera.reverse_engineering.snapshots.repository import InMemorySnapshotStorage
from dera.reverse_engineering.snapshots.storage import SnapshotFilter, SnapshotStorage


class ReverseEngineeringService:
    """Singleton/per-app coordination service for reverse engineering state and operations."""

    def __init__(self, snapshot_storage: SnapshotStorage | None = None) -> None:
        self._schemas: dict[tuple[str, str], SchemaRepresentation] = {}
        self._graphs: dict[tuple[str, str], ForeignKeyGraph] = {}
        self._dependencies: dict[tuple[str, str], DependencyAnalysisResult] = {}
        self._snapshot_storage = snapshot_storage or InMemorySnapshotStorage()
        self._export_service = ExportService()
        self._export_artifacts: dict[tuple[str, str], ExportArtifact] = {}
        self._export_jobs: dict[tuple[str, str], dict[str, Any]] = {}

    # --- Schema Management ---

    def register_schema(self, workspace_id: str, schema: SchemaRepresentation) -> None:
        """Register an analyzed schema representation within an authorized workspace."""
        key = (workspace_id, schema.database.id)
        self._schemas[key] = schema
        # Invalidate cached graph and dependency results
        self._graphs.pop(key, None)
        self._dependencies.pop(key, None)

    def get_schema(self, workspace_id: str, schema_id: str) -> SchemaRepresentation | None:
        """Retrieve authorized schema representation by ID."""
        return self._schemas.get((workspace_id, schema_id))

    def list_schemas(self, workspace_id: str) -> list[SchemaRepresentation]:
        """List all schemas registered within the designated workspace."""
        return [schema for (ws, _), schema in self._schemas.items() if ws == workspace_id]

    # --- Graph & Dependency Computation ---

    def get_relationship_graph(self, workspace_id: str, schema_id: str) -> ForeignKeyGraph | None:
        """Retrieve or compute the foreign key relationship graph for an authorized schema."""
        key = (workspace_id, schema_id)
        if key in self._graphs:
            return self._graphs[key]

        schema = self.get_schema(workspace_id, schema_id)
        if not schema:
            return None

        builder = ForeignKeyGraphBuilder()
        graph = builder.build(schema)
        self._graphs[key] = graph
        return graph

    def get_dependency_analysis(
        self,
        workspace_id: str,
        schema_id: str,
    ) -> DependencyAnalysisResult | None:
        """Retrieve or compute dependency analysis and cycle reports for an authorized schema."""
        key = (workspace_id, schema_id)
        if key in self._dependencies:
            return self._dependencies[key]

        schema = self.get_schema(workspace_id, schema_id)
        if not schema:
            return None

        graph = self.get_relationship_graph(workspace_id, schema_id)
        analyzer = DependencyAnalyzer()
        res = analyzer.analyze(schema, graph)
        self._dependencies[key] = res
        return res

    # --- Snapshots ---

    @property
    def snapshot_storage(self) -> SnapshotStorage:
        """Active storage repository for schema snapshots."""
        return self._snapshot_storage

    async def create_snapshot(
        self,
        workspace_id: str,
        schema_id: str,
        tags: list[str] | None = None,
        requester_id: str | None = None,
    ) -> SchemaSnapshot | None:
        """Build and persist an immutable schema snapshot from verified schema representation."""
        schema = self.get_schema(workspace_id, schema_id)
        if not schema:
            return None

        graph = self.get_relationship_graph(workspace_id, schema_id)
        dependencies = self.get_dependency_analysis(workspace_id, schema_id)

        snapshot = SchemaSnapshotBuilder.from_analysis(
            schema=schema,
            relationships=graph,
            dependencies=dependencies,
            workspace_id=workspace_id,
            requester_id=requester_id,
            tags=tuple(tags or []),
        )
        await self._snapshot_storage.save(snapshot)
        return snapshot

    async def get_snapshot(self, workspace_id: str, snapshot_id: str) -> SchemaSnapshot | None:
        """Retrieve authorized snapshot by ID."""
        return await self._snapshot_storage.get_by_id(snapshot_id, workspace_id)

    async def list_snapshots(
        self,
        workspace_id: str,
        database_id: str | None = None,
        fingerprint: str | None = None,
    ) -> list[SchemaSnapshot]:
        """List snapshots matching criteria within workspace boundary."""
        filter_criteria = SnapshotFilter(
            workspace_id=workspace_id,
            database_id=database_id,
            fingerprint=fingerprint,
        )
        return await self._snapshot_storage.list_snapshots(filter_criteria)

    async def verify_snapshot(
        self, workspace_id: str, snapshot_id: str
    ) -> SnapshotIntegrityReport | None:
        """Verify cryptographic integrity of an authorized snapshot."""
        snapshot = await self.get_snapshot(workspace_id, snapshot_id)
        if not snapshot:
            return None
        return verify_snapshot_integrity(snapshot)

    # --- Exports ---

    def create_export(
        self,
        workspace_id: str,
        options: ExportOptions,
        schema_id: str | None = None,
        snapshot_id: str | None = None,
    ) -> tuple[str, ExportArtifact]:
        """Generate a deterministic export artifact and cache it for authorized download."""
        schema = self.get_schema(workspace_id, schema_id) if schema_id else None
        graph = self.get_relationship_graph(workspace_id, schema_id) if schema_id else None
        dependencies = self.get_dependency_analysis(workspace_id, schema_id) if schema_id else None

        export_id = f"exp_{uuid.uuid4().hex}"
        artifact = self._export_service.generate_export(
            options=options,
            schema=schema,
            graph=graph,
            dependencies=dependencies,
            snapshot=None,
        )

        key = (workspace_id, export_id)
        self._export_artifacts[key] = artifact
        self._export_jobs[key] = {
            "export_id": export_id,
            "job_id": f"job_{uuid.uuid4().hex}",
            "status": "succeeded",
            "format": options.format.value,
            "scope": options.scope.value,
            "created_at": datetime.now(UTC),
            "completed_at": datetime.now(UTC),
            "error_message": None,
        }
        return export_id, artifact

    def get_export_job(self, workspace_id: str, export_id: str) -> dict[str, Any] | None:
        """Retrieve export job metadata."""
        return self._export_jobs.get((workspace_id, export_id))

    def get_export_artifact(self, workspace_id: str, export_id: str) -> ExportArtifact | None:
        """Retrieve raw export artifact for download."""
        return self._export_artifacts.get((workspace_id, export_id))


# Global default service singleton
default_reverse_engineering_service = ReverseEngineeringService()
