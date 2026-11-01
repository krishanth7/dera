"""DERA Comparison — Phase 9.1 Core Domain Models.

Defines strongly typed, immutable Pydantic v2 domain models for comparison
configuration, individual schema changes, metrics summaries, and complete diff reports.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from dera.comparison.enums import (
    ComparisonChangeType,
    ComparisonObjectType,
    ComparisonStatus,
)
from dera.comparison.evidence import ObjectEvidence, PropertyDifference
from dera.comparison.fingerprint import (
    compute_change_fingerprint,
    compute_configuration_fingerprint,
    compute_report_fingerprint,
)
from dera.metadata.enums import MetadataCompleteness

COMPARATOR_ENGINE_VERSION = "dera.comparator.v1"


class ComparisonConfig(BaseModel):
    """Configuration options governing schema comparison execution."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    included_namespaces: tuple[str, ...] | None = Field(
        default=None,
        description="Optional filter whitelist of namespaces to include.",
    )
    excluded_namespaces: tuple[str, ...] = Field(
        default_factory=tuple,
        description="List of namespaces to exclude (e.g. internal schemas).",
    )
    included_object_types: tuple[ComparisonObjectType, ...] | None = Field(
        default=None,
        description="Filter whitelist of object types to compare.",
    )
    ignore_column_order: bool = Field(
        default=False,
        description="If True, ordinal position differences are not reported as modifications.",
    )
    ignore_comments: bool = Field(
        default=False,
        description="If True, table and column comment modifications are ignored.",
    )
    allow_compatible_engine_families: bool = Field(
        default=True,
        description="If True, cross-engine comparisons within compatible families (e.g. Postgres -> Supabase) are permitted.",
    )

    def to_canonical_dict(self) -> dict[str, Any]:
        """Convert config to canonical dictionary for fingerprint generation."""
        return {
            "included_namespaces": sorted(self.included_namespaces)
            if self.included_namespaces
            else None,
            "excluded_namespaces": sorted(self.excluded_namespaces),
            "included_object_types": (
                sorted(t.value for t in self.included_object_types)
                if self.included_object_types
                else None
            ),
            "ignore_column_order": self.ignore_column_order,
            "ignore_comments": self.ignore_comments,
            "allow_compatible_engine_families": self.allow_compatible_engine_families,
        }

    @property
    def fingerprint(self) -> str:
        """Stable configuration fingerprint."""
        return compute_configuration_fingerprint(self.to_canonical_dict())


class SchemaChange(BaseModel):
    """Verifiable structural difference record for a canonical schema object."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    change_id: str = Field(description="Unique deterministic identifier (e.g. 'chg_...').")
    change_type: ComparisonChangeType = Field(
        description="Classification (ADDED, REMOVED, MODIFIED, etc.)."
    )
    object_type: ComparisonObjectType = Field(description="Type of object changed.")
    canonical_id: str = Field(description="Canonical ObjectId of the object.")
    namespace: str = Field(description="Namespace / schema of the target or baseline object.")
    name: str = Field(description="Native object name.")
    parent_canonical_id: str | None = Field(
        default=None,
        description="Canonical ObjectId of parent table if object is a child element (column, index, constraint).",
    )
    parent_name: str | None = Field(
        default=None,
        description="Native name of parent table if applicable.",
    )
    before_evidence: ObjectEvidence | None = Field(
        default=None,
        description="Evidence payload from baseline snapshot if present.",
    )
    after_evidence: ObjectEvidence | None = Field(
        default=None,
        description="Evidence payload from target snapshot if present.",
    )
    property_differences: tuple[PropertyDifference, ...] = Field(
        default_factory=tuple,
        description="Detailed list of specific modified property values.",
    )
    metadata_completeness: MetadataCompleteness = Field(
        default=MetadataCompleteness.COMPLETE,
        description="Effective metadata completeness for this change.",
    )
    engine: str = Field(description="Source database engine.")
    comparator_version: str = Field(
        default=COMPARATOR_ENGINE_VERSION,
        description="Version string of comparison rules/comparator.",
    )
    fingerprint: str = Field(
        default="",
        description="Reproducible SHA-256 fingerprint for this specific difference.",
    )

    @classmethod
    def create(
        cls,
        change_type: ComparisonChangeType,
        object_type: ComparisonObjectType,
        canonical_id: str,
        namespace: str,
        name: str,
        engine: str,
        parent_canonical_id: str | None = None,
        parent_name: str | None = None,
        before_evidence: ObjectEvidence | None = None,
        after_evidence: ObjectEvidence | None = None,
        property_differences: tuple[PropertyDifference, ...] = (),
        metadata_completeness: MetadataCompleteness = MetadataCompleteness.COMPLETE,
        comparator_version: str = COMPARATOR_ENGINE_VERSION,
    ) -> SchemaChange:
        """Factory method computing change_id and fingerprint deterministically."""
        changed_props = tuple(d.property_name for d in property_differences)
        before_props = before_evidence.properties if before_evidence else None
        after_props = after_evidence.properties if after_evidence else None

        fp = compute_change_fingerprint(
            comparator_version=comparator_version,
            object_type=object_type.value,
            canonical_id=canonical_id,
            change_type=change_type.value,
            before_properties=before_props,
            after_properties=after_props,
            changed_properties=changed_props,
        )
        change_id = f"chg_{fp[:16]}"
        return cls(
            change_id=change_id,
            change_type=change_type,
            object_type=object_type,
            canonical_id=canonical_id,
            namespace=namespace,
            name=name,
            parent_canonical_id=parent_canonical_id,
            parent_name=parent_name,
            before_evidence=before_evidence,
            after_evidence=after_evidence,
            property_differences=property_differences,
            metadata_completeness=metadata_completeness,
            engine=engine,
            comparator_version=comparator_version,
            fingerprint=fp,
        )


class ComparisonSummary(BaseModel):
    """Aggregated structural difference counts and metrics."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    total_changes: int = Field(default=0, description="Total count of reported changes.")
    total_added: int = Field(default=0, description="Count of added objects.")
    total_removed: int = Field(default=0, description="Count of removed objects.")
    total_modified: int = Field(default=0, description="Count of modified objects.")
    total_unchanged: int = Field(default=0, description="Count of evaluated unchanged objects.")
    total_unsupported: int = Field(default=0, description="Count of unsupported comparisons.")
    total_indeterminate: int = Field(default=0, description="Count of indeterminate comparisons.")
    changes_by_object_type: dict[str, int] = Field(
        default_factory=dict,
        description="Change count broken down by ComparisonObjectType.",
    )
    changes_by_namespace: dict[str, int] = Field(
        default_factory=dict,
        description="Change count broken down by namespace.",
    )


class ComparisonReport(BaseModel):
    """Complete, immutable schema snapshot comparison report."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    report_id: str = Field(description="Unique deterministic identifier (e.g. 'rpt_...').")
    comparator_version: str = Field(
        default=COMPARATOR_ENGINE_VERSION,
        description="Comparator engine version.",
    )
    baseline_snapshot_id: str = Field(description="Snapshot ID of baseline.")
    baseline_fingerprint: str = Field(description="Cryptographic fingerprint of baseline payload.")
    target_snapshot_id: str = Field(description="Snapshot ID of target.")
    target_fingerprint: str = Field(description="Cryptographic fingerprint of target payload.")
    engine: str = Field(description="Database engine of baseline snapshot.")
    target_engine: str = Field(description="Database engine of target snapshot.")
    configuration_fingerprint: str = Field(
        description="Fingerprint of applied comparison configuration."
    )
    status: ComparisonStatus = Field(description="Overall comparison status.")
    summary: ComparisonSummary = Field(description="Aggregated change metrics.")
    changes: tuple[SchemaChange, ...] = Field(
        default_factory=tuple,
        description="Ordered sequence of canonical schema differences.",
    )
    metadata_limitations: tuple[str, ...] = Field(
        default_factory=tuple,
        description="Documented completeness or support limitations encountered.",
    )
    report_fingerprint: str = Field(
        default="",
        description="Stable cryptographic digest over complete diff report content.",
    )

    @classmethod
    def create(
        cls,
        baseline_snapshot_id: str,
        baseline_fingerprint: str,
        target_snapshot_id: str,
        target_fingerprint: str,
        engine: str,
        target_engine: str,
        config: ComparisonConfig,
        status: ComparisonStatus,
        summary: ComparisonSummary,
        changes: tuple[SchemaChange, ...],
        metadata_limitations: tuple[str, ...] = (),
        comparator_version: str = COMPARATOR_ENGINE_VERSION,
    ) -> ComparisonReport:
        """Construct report and compute stable report fingerprint."""
        change_fps = tuple(c.fingerprint for c in changes)
        rpt_fp = compute_report_fingerprint(
            baseline_fingerprint=baseline_fingerprint,
            target_fingerprint=target_fingerprint,
            config_fingerprint=config.fingerprint,
            change_fingerprints=change_fps,
        )
        report_id = f"rpt_{rpt_fp[:16]}"
        return cls(
            report_id=report_id,
            comparator_version=comparator_version,
            baseline_snapshot_id=baseline_snapshot_id,
            baseline_fingerprint=baseline_fingerprint,
            target_snapshot_id=target_snapshot_id,
            target_fingerprint=target_fingerprint,
            engine=engine,
            target_engine=target_engine,
            configuration_fingerprint=config.fingerprint,
            status=status,
            summary=summary,
            changes=changes,
            metadata_limitations=metadata_limitations,
            report_fingerprint=rpt_fp,
        )
