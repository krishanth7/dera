"""DERA Reverse Engineering — Phase 6.5 Snapshot Storage Contract.

Defines the abstract SnapshotStorage interface and filtering contracts for safe,
tenant-isolated persistence and retrieval of schema snapshots.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

from dera.metadata.enums import MetadataCompleteness

if TYPE_CHECKING:
    from dera.reverse_engineering.snapshots.integrity import SnapshotIntegrityReport
    from dera.reverse_engineering.snapshots.models import SchemaSnapshot


class SnapshotFilter(BaseModel):
    """Filter criteria for searching and paginating stored snapshots."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    workspace_id: str = Field(description="Mandatory workspace identifier for tenant isolation.")
    database_name: str | None = Field(default=None, description="Optional database name filter.")
    engine: str | None = Field(default=None, description="Optional engine type filter.")
    structural_fingerprint: str | None = Field(
        default=None,
        description="Optional structural SHA-256 fingerprint match.",
    )
    completeness: MetadataCompleteness | None = Field(
        default=None,
        description="Optional metadata completeness filter.",
    )
    tag_key: str | None = Field(default=None, description="Optional tag key match.")
    tag_value: str | None = Field(default=None, description="Optional tag value match.")
    created_after: datetime | None = Field(
        default=None, description="Filter for snapshots created >= timestamp."
    )
    created_before: datetime | None = Field(
        default=None, description="Filter for snapshots created <= timestamp."
    )
    limit: int = Field(default=100, ge=1, le=1000, description="Pagination result limit.")
    offset: int = Field(default=0, ge=0, description="Pagination offset.")


class SnapshotStorage(ABC):
    """Abstract interface for snapshot persistence, retrieval, and integrity verification."""

    @abstractmethod
    async def save(self, snapshot: SchemaSnapshot) -> None:
        """Persist a SchemaSnapshot atomically.

        Args:
            snapshot: The SchemaSnapshot to persist.

        Raises:
            SnapshotStorageError: If persistence fails or overwriting immutable record is attempted.
        """

    @abstractmethod
    async def get_by_id(self, snapshot_id: str, workspace_id: str) -> SchemaSnapshot | None:
        """Retrieve a snapshot by ID within an authorized workspace.

        Args:
            snapshot_id: Snapshot record identifier.
            workspace_id: Authorized workspace identifier.

        Returns:
            SchemaSnapshot if found and authorized, None otherwise.
        """

    @abstractmethod
    async def get_by_fingerprint(
        self,
        fingerprint: str,
        workspace_id: str,
    ) -> list[SchemaSnapshot]:
        """Retrieve all snapshots matching a structural fingerprint within a workspace.

        Args:
            fingerprint: 64-char hex SHA-256 structural fingerprint.
            workspace_id: Authorized workspace identifier.

        Returns:
            List of matching snapshots.
        """

    @abstractmethod
    async def list_snapshots(self, filter_params: SnapshotFilter) -> list[SchemaSnapshot]:
        """Query snapshots matching the specified filter criteria within the workspace.

        Args:
            filter_params: Filter criteria including workspace_id, engine, dates, and pagination.

        Returns:
            List of matching SchemaSnapshot records.
        """

    @abstractmethod
    async def delete(self, snapshot_id: str, workspace_id: str) -> bool:
        """Authorized deletion of a snapshot record.

        Args:
            snapshot_id: Snapshot to delete.
            workspace_id: Authorized workspace.

        Returns:
            True if deleted, False if not found.
        """

    @abstractmethod
    async def verify(self, snapshot_id: str, workspace_id: str) -> SnapshotIntegrityReport:
        """Perform cryptographic integrity verification on a stored snapshot.

        Args:
            snapshot_id: Snapshot to verify.
            workspace_id: Authorized workspace.

        Returns:
            SnapshotIntegrityReport detailing whether the stored snapshot is intact.
        """
