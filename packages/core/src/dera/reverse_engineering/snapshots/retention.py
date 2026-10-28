"""DERA Reverse Engineering — Phase 6.5 Snapshot Retention Controls.

Provides rule-based lifecycle management for schema snapshots, enforcing retention periods,
count limits, tag protections, and unique fingerprint preservation.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

from dera.reverse_engineering.snapshots.storage import SnapshotFilter

if TYPE_CHECKING:
    from dera.reverse_engineering.snapshots.models import SchemaSnapshot
    from dera.reverse_engineering.snapshots.storage import SnapshotStorage


class SnapshotRetentionPolicy(BaseModel):
    """Retention configuration controlling snapshot aging and count quotas."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    max_snapshots_per_database: int | None = Field(
        default=None,
        ge=1,
        description="Maximum retained snapshots per database name.",
    )
    max_age_days: int | None = Field(
        default=None,
        ge=1,
        description="Maximum age in days before a snapshot is eligible for expiration.",
    )
    protected_tags: tuple[str, ...] = Field(
        default=("production", "baseline", "gold", "permanent"),
        description="Tag keys whose presence prevents automatic pruning.",
    )
    preserve_unique_fingerprints: bool = Field(
        default=True,
        description="If True, retains at least one snapshot per distinct structural fingerprint.",
    )


class RetentionEvaluationResult(BaseModel):
    """Result of evaluating a set of snapshots against a retention policy."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    total_evaluated: int = Field(description="Total snapshots inspected.")
    retained_snapshot_ids: tuple[str, ...] = Field(
        description="Snapshot IDs designated for retention."
    )
    expired_snapshot_ids: tuple[str, ...] = Field(
        description="Snapshot IDs designated for expiration/pruning."
    )
    protected_snapshot_ids: tuple[str, ...] = Field(
        description="Snapshot IDs protected from expiration by tags/rules."
    )
    reasons: dict[str, str] = Field(
        default_factory=dict,
        description="Audit mapping of snapshot_id to retention/expiration rationale.",
    )


class RetentionActionResult(BaseModel):
    """Execution summary after applying a retention policy to a storage backend."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    workspace_id: str = Field(description="Workspace identifier.")
    database_name: str = Field(description="Database name targeted.")
    evaluation: RetentionEvaluationResult = Field(description="Underlying retention evaluation.")
    deleted_count: int = Field(description="Number of snapshots deleted from storage.")
    failed_deletions: dict[str, str] = Field(
        default_factory=dict,
        description="Mapping of snapshot_id to deletion error message if any failed.",
    )
    dry_run: bool = Field(default=False, description="True if execution was simulated.")


class RetentionManager:
    """Manages evaluation and safe application of retention policies to snapshot storage."""

    @classmethod
    def evaluate(
        cls,
        snapshots: list[SchemaSnapshot],
        policy: SnapshotRetentionPolicy,
        now: datetime | None = None,
    ) -> RetentionEvaluationResult:
        """Evaluate a list of snapshots against a retention policy without modifying storage.

        Args:
            snapshots: List of SchemaSnapshot instances (should belong to one database).
            policy: Retention policy rules.
            now: Current reference timestamp (UTC).

        Returns:
            RetentionEvaluationResult with categorized snapshot IDs and rationales.
        """
        ref_time = now or datetime.now(UTC)
        if ref_time.tzinfo is None:
            ref_time = ref_time.replace(tzinfo=UTC)

        # Sort newest to oldest
        sorted_snaps = sorted(
            snapshots,
            key=lambda s: (s.envelope.capture_timestamp, s.snapshot_id),
            reverse=True,
        )

        retained: set[str] = set()
        expired: set[str] = set()
        protected: set[str] = set()
        reasons: dict[str, str] = {}

        # 1. Identify protected snapshots (tags)
        for s in sorted_snaps:
            has_protected_tag = any(tag in s.envelope.tags for tag in policy.protected_tags)
            if has_protected_tag:
                protected.add(s.snapshot_id)
                retained.add(s.snapshot_id)
                reasons[s.snapshot_id] = "Protected by tag"

        # 2. Identify unique fingerprints to preserve
        preserved_fps: set[str] = set()
        if policy.preserve_unique_fingerprints:
            for s in sorted_snaps:
                if s.fingerprint not in preserved_fps:
                    preserved_fps.add(s.fingerprint)
                    retained.add(s.snapshot_id)
                    if s.snapshot_id not in reasons:
                        reasons[s.snapshot_id] = (
                            f"Preserved as unique fingerprint {s.fingerprint[:8]}"
                        )

        # 3. Check age expiration
        if policy.max_age_days is not None:
            max_delta = timedelta(days=policy.max_age_days)
            for s in sorted_snaps:
                if s.snapshot_id in protected:
                    continue
                if (ref_time - s.envelope.capture_timestamp) > max_delta:
                    # If already marked retained by unique fingerprint, don't expire
                    if policy.preserve_unique_fingerprints and s.snapshot_id in retained:
                        continue
                    expired.add(s.snapshot_id)
                    reasons[s.snapshot_id] = f"Exceeded max age of {policy.max_age_days} days"

        # 4. Check max count per database
        if policy.max_snapshots_per_database is not None:
            eligible_count = 0
            for s in sorted_snaps:
                if s.snapshot_id in protected or (
                    policy.preserve_unique_fingerprints
                    and s.snapshot_id in retained
                    and s.snapshot_id not in expired
                ):
                    continue

                if s.snapshot_id in expired:
                    continue

                eligible_count += 1
                if eligible_count > policy.max_snapshots_per_database:
                    expired.add(s.snapshot_id)
                    reasons[s.snapshot_id] = (
                        f"Exceeded max snapshot count ({policy.max_snapshots_per_database})"
                    )
                else:
                    retained.add(s.snapshot_id)
                    if s.snapshot_id not in reasons:
                        reasons[s.snapshot_id] = "Within count quota"

        # Snapshots neither expired nor protected are retained
        for s in sorted_snaps:
            if s.snapshot_id not in expired:
                retained.add(s.snapshot_id)
                if s.snapshot_id not in reasons:
                    reasons[s.snapshot_id] = "Active snapshot"

        return RetentionEvaluationResult(
            total_evaluated=len(snapshots),
            retained_snapshot_ids=tuple(sorted(retained)),
            expired_snapshot_ids=tuple(sorted(expired)),
            protected_snapshot_ids=tuple(sorted(protected)),
            reasons=reasons,
        )

    @classmethod
    async def apply(
        cls,
        storage: SnapshotStorage,
        workspace_id: str,
        database_name: str,
        policy: SnapshotRetentionPolicy,
        dry_run: bool = False,
    ) -> RetentionActionResult:
        """Evaluate and apply retention rules to stored snapshots for a specific database."""
        # Query all snapshots for this workspace and database
        filter_params = SnapshotFilter(
            workspace_id=workspace_id,
            database_name=database_name,
            limit=1000,
        )
        snapshots = await storage.list_snapshots(filter_params)
        evaluation = cls.evaluate(snapshots, policy)

        deleted = 0
        failures: dict[str, str] = {}

        if not dry_run:
            for snap_id in evaluation.expired_snapshot_ids:
                try:
                    success = await storage.delete(snap_id, workspace_id)
                    if success:
                        deleted += 1
                    else:
                        failures[snap_id] = "Snapshot not found during deletion"
                except Exception as exc:
                    failures[snap_id] = str(exc)

        return RetentionActionResult(
            workspace_id=workspace_id,
            database_name=database_name,
            evaluation=evaluation,
            deleted_count=deleted,
            failed_deletions=failures,
            dry_run=dry_run,
        )
