"""DERA Comparison — Phase 9.1 Schema Comparison Engine.

Orchestrates deterministic, explainable, and reproducible structural comparison
between two immutable canonical schema snapshots.

Features:
- Fingerprint fast-path: Instant empty-diff report when structural fingerprints match.
- Strict input immutability: Snapshots are never mutated.
- Safety bounding: Checks table, column, and difference limits.
- Engine compatibility enforcement.
- Canonical object matching and granular property-level before/after evidence.
- Deterministic ordering of all output differences.
- Zero AI / LLM / external heuristic dependency.
"""

from __future__ import annotations

from dera.comparison.comparators.namespaces import NamespaceComparator
from dera.comparison.comparators.relationships import RelationshipComparator
from dera.comparison.comparators.tables import TableComparator
from dera.comparison.comparators.views import ViewComparator
from dera.comparison.compatibility import SnapshotCompatibilityValidator
from dera.comparison.enums import ComparisonObjectType, ComparisonStatus
from dera.comparison.limits import ComparisonResourceLimits
from dera.comparison.models import (
    COMPARATOR_ENGINE_VERSION,
    ComparisonConfig,
    ComparisonReport,
    ComparisonSummary,
    SchemaChange,
)
from dera.comparison.ordering import sort_schema_changes
from dera.comparison.summary import compute_comparison_summary
from dera.reverse_engineering.snapshots.models import SchemaSnapshot


class SchemaComparisonEngine:
    """Primary deterministic comparison engine for Phase 9.1."""

    def __init__(
        self,
        limits: ComparisonResourceLimits | None = None,
        comparator_version: str = COMPARATOR_ENGINE_VERSION,
    ) -> None:
        self.limits = limits or ComparisonResourceLimits()
        self.comparator_version = comparator_version

    def compare(
        self,
        baseline: SchemaSnapshot,
        target: SchemaSnapshot,
        config: ComparisonConfig | None = None,
    ) -> ComparisonReport:
        """Compare two immutable snapshots and return an explainable diff report.

        Args:
            baseline: Immutable baseline SchemaSnapshot.
            target: Immutable target SchemaSnapshot.
            config: Optional comparison configuration.

        Returns:
            ComparisonReport containing ordered differences, summary, and fingerprints.
        """
        effective_config = config or ComparisonConfig()

        # 1. Compatibility check
        compat_result = SnapshotCompatibilityValidator.validate(
            baseline=baseline,
            target=target,
            allow_compatible_engine_families=effective_config.allow_compatible_engine_families,
        )

        # 2. Resource limits pre-flight checks
        b_tables = baseline.payload.tables
        t_tables = target.payload.tables
        self.limits.check_table_count(len(b_tables), label="baseline snapshot")
        self.limits.check_table_count(len(t_tables), label="target snapshot")

        b_cols = sum(len(t.columns) for t in b_tables)
        t_cols = sum(len(t.columns) for t in t_tables)
        self.limits.check_column_count(b_cols, label="baseline snapshot")
        self.limits.check_column_count(t_cols, label="target snapshot")

        # 3. Cryptographic Fingerprint Fast-Path
        # If fingerprints match and no subset filters are configured, schemas are identical
        if (
            baseline.fingerprint == target.fingerprint
            and baseline.payload.engine == target.payload.engine
            and effective_config.included_namespaces is None
            and not effective_config.excluded_namespaces
            and effective_config.included_object_types is None
        ):
            summary = ComparisonSummary(
                total_changes=0,
                total_added=0,
                total_removed=0,
                total_modified=0,
                total_unchanged=len(b_tables),
            )
            return ComparisonReport.create(
                baseline_snapshot_id=baseline.snapshot_id,
                baseline_fingerprint=baseline.fingerprint,
                target_snapshot_id=target.snapshot_id,
                target_fingerprint=target.fingerprint,
                engine=baseline.payload.engine,
                target_engine=target.payload.engine,
                config=effective_config,
                status=ComparisonStatus.IDENTICAL,
                summary=summary,
                changes=(),
                metadata_limitations=compat_result.notes,
                comparator_version=self.comparator_version,
            )

        # 4. Execute Granular Comparators
        raw_changes: list[SchemaChange] = []
        limitations: list[str] = list(compat_result.notes)

        # Check metadata completeness limitations
        if baseline.completeness != target.completeness:
            limitations.append(
                f"Metadata completeness mismatch: baseline is {baseline.completeness.value}, "
                f"target is {target.completeness.value}."
            )

        # Namespaces
        if self._is_type_included(ComparisonObjectType.NAMESPACE, effective_config):
            raw_changes.extend(
                NamespaceComparator.compare(
                    baseline=baseline,
                    target=target,
                    config=effective_config,
                )
            )

        # Tables (and child columns, constraints, indexes)
        if (
            self._is_type_included(ComparisonObjectType.TABLE, effective_config)
            or self._is_type_included(ComparisonObjectType.COLUMN, effective_config)
            or self._is_type_included(ComparisonObjectType.PRIMARY_KEY, effective_config)
            or self._is_type_included(ComparisonObjectType.FOREIGN_KEY, effective_config)
            or self._is_type_included(ComparisonObjectType.UNIQUE_CONSTRAINT, effective_config)
            or self._is_type_included(ComparisonObjectType.CHECK_CONSTRAINT, effective_config)
            or self._is_type_included(ComparisonObjectType.INDEX, effective_config)
        ):
            table_changes = TableComparator.compare_tables(
                baseline=baseline,
                target=target,
                config=effective_config,
            )
            # Filter by included_object_types if restricted
            if effective_config.included_object_types is not None:
                table_changes = [
                    c
                    for c in table_changes
                    if c.object_type in effective_config.included_object_types
                ]
            raw_changes.extend(table_changes)

        # Views
        if self._is_type_included(ComparisonObjectType.VIEW, effective_config):
            raw_changes.extend(
                ViewComparator.compare_views(
                    baseline=baseline,
                    target=target,
                    config=effective_config,
                )
            )

        # Relationships
        if self._is_type_included(ComparisonObjectType.RELATIONSHIP, effective_config):
            raw_changes.extend(
                RelationshipComparator.compare_relationships(
                    baseline=baseline,
                    target=target,
                    config=effective_config,
                )
            )

        # 5. Check generated difference bounds
        self.limits.check_difference_count(len(raw_changes))

        # 6. Deterministic Ordering
        sorted_changes = sort_schema_changes(raw_changes)

        # 7. Summary calculation
        summary = compute_comparison_summary(sorted_changes)
        status = (
            ComparisonStatus.IDENTICAL
            if len(sorted_changes) == 0
            else ComparisonStatus.DIFFERENCES_FOUND
        )

        return ComparisonReport.create(
            baseline_snapshot_id=baseline.snapshot_id,
            baseline_fingerprint=baseline.fingerprint,
            target_snapshot_id=target.snapshot_id,
            target_fingerprint=target.fingerprint,
            engine=baseline.payload.engine,
            target_engine=target.payload.engine,
            config=effective_config,
            status=status,
            summary=summary,
            changes=sorted_changes,
            metadata_limitations=tuple(limitations),
            comparator_version=self.comparator_version,
        )

    @staticmethod
    def _is_type_included(obj_type: ComparisonObjectType, config: ComparisonConfig) -> bool:
        if config.included_object_types is None:
            return True
        return obj_type in config.included_object_types
