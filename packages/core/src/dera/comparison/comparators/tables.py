"""DERA Comparison — Phase 9.1 Table Comparator.

Detects added, removed, and modified tables:
- Table existence (added/removed)
- Table classification / table_type changes
- Table comments (if not ignored)
- Granular child differences (delegated to ColumnComparator, ConstraintComparator, IndexComparator)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from dera.comparison.comparators.columns import ColumnComparator
from dera.comparison.comparators.constraints import ConstraintComparator
from dera.comparison.comparators.indexes import IndexComparator
from dera.comparison.enums import (
    ComparisonChangeType,
    ComparisonObjectType,
    PropertyComparisonStatus,
)
from dera.comparison.evidence import ObjectEvidence, PropertyDifference
from dera.comparison.matching import match_by_key, table_canonical_key
from dera.comparison.models import SchemaChange
from dera.comparison.ordering import sort_property_differences
from dera.metadata.enums import MetadataCompleteness
from dera.reverse_engineering.snapshots.models import (
    SnapshotTablePayload,
)

if TYPE_CHECKING:
    from dera.comparison.models import ComparisonConfig
    from dera.reverse_engineering.snapshots.models import SchemaSnapshot


class TableComparator:
    """Compares tables and delegates child column/constraint/index comparisons."""

    @classmethod
    def compare_tables(
        cls,
        baseline: SchemaSnapshot,
        target: SchemaSnapshot,
        config: ComparisonConfig,
    ) -> list[SchemaChange]:
        """Produce SchemaChange records for all table and contained child object differences."""
        changes: list[SchemaChange] = []

        b_tables = [
            t
            for t in baseline.payload.tables
            if cls._is_namespace_allowed(t.namespace, config)
        ]
        t_tables = [
            t
            for t in target.payload.tables
            if cls._is_namespace_allowed(t.namespace, config)
        ]

        matches = match_by_key(
            baseline_items=b_tables,
            target_items=t_tables,
            key_fn=table_canonical_key,
        )

        for match in matches:
            if match.is_removed:
                b_tbl: SnapshotTablePayload = match.baseline
                before_ev = ObjectEvidence(
                    snapshot_id=baseline.snapshot_id,
                    object_id=b_tbl.table_id,
                    namespace=b_tbl.namespace,
                    name=b_tbl.name,
                    properties={
                        "table_type": b_tbl.table_type.value,
                        "comment": b_tbl.comment,
                        "column_count": len(b_tbl.columns),
                        "index_count": len(b_tbl.indexes),
                    },
                    completeness=baseline.payload.completeness,
                )
                # Record table removal
                changes.append(
                    SchemaChange.create(
                        change_type=ComparisonChangeType.REMOVED,
                        object_type=ComparisonObjectType.TABLE,
                        canonical_id=b_tbl.table_id,
                        namespace=b_tbl.namespace,
                        name=b_tbl.name,
                        engine=baseline.payload.engine,
                        before_evidence=before_ev,
                        after_evidence=None,
                        metadata_completeness=baseline.payload.completeness,
                    )
                )

            elif match.is_added:
                t_tbl: SnapshotTablePayload = match.target
                after_ev = ObjectEvidence(
                    snapshot_id=target.snapshot_id,
                    object_id=t_tbl.table_id,
                    namespace=t_tbl.namespace,
                    name=t_tbl.name,
                    properties={
                        "table_type": t_tbl.table_type.value,
                        "comment": t_tbl.comment,
                        "column_count": len(t_tbl.columns),
                        "index_count": len(t_tbl.indexes),
                    },
                    completeness=target.payload.completeness,
                )
                # Record table addition
                changes.append(
                    SchemaChange.create(
                        change_type=ComparisonChangeType.ADDED,
                        object_type=ComparisonObjectType.TABLE,
                        canonical_id=t_tbl.table_id,
                        namespace=t_tbl.namespace,
                        name=t_tbl.name,
                        engine=target.payload.engine,
                        before_evidence=None,
                        after_evidence=after_ev,
                        metadata_completeness=target.payload.completeness,
                    )
                )

            elif match.is_both:
                b_tbl = match.baseline
                t_tbl = match.target
                prop_diffs: list[PropertyDifference] = []

                # 1. Table Type
                if b_tbl.table_type != t_tbl.table_type:
                    prop_diffs.append(
                        PropertyDifference(
                            property_name="table_type",
                            before_value=b_tbl.table_type.value,
                            after_value=t_tbl.table_type.value,
                            status=PropertyComparisonStatus.MODIFIED,
                        )
                    )

                # 2. Table Comment
                if not config.ignore_comments:
                    if b_tbl.comment != t_tbl.comment:
                        prop_diffs.append(
                            PropertyDifference(
                                property_name="comment",
                                before_value=b_tbl.comment,
                                after_value=t_tbl.comment,
                                status=PropertyComparisonStatus.MODIFIED,
                            )
                        )

                # Table-level metadata modification
                effective_completeness = (
                    MetadataCompleteness.COMPLETE
                    if baseline.payload.completeness == MetadataCompleteness.COMPLETE
                    and target.payload.completeness == MetadataCompleteness.COMPLETE
                    else MetadataCompleteness.PARTIAL
                )

                if prop_diffs:
                    sorted_diffs = sort_property_differences(prop_diffs)
                    before_ev = ObjectEvidence(
                        snapshot_id=baseline.snapshot_id,
                        object_id=b_tbl.table_id,
                        namespace=b_tbl.namespace,
                        name=b_tbl.name,
                        properties={
                            "table_type": b_tbl.table_type.value,
                            "comment": b_tbl.comment,
                        },
                        completeness=baseline.payload.completeness,
                    )
                    after_ev = ObjectEvidence(
                        snapshot_id=target.snapshot_id,
                        object_id=t_tbl.table_id,
                        namespace=t_tbl.namespace,
                        name=t_tbl.name,
                        properties={
                            "table_type": t_tbl.table_type.value,
                            "comment": t_tbl.comment,
                        },
                        completeness=target.payload.completeness,
                    )
                    changes.append(
                        SchemaChange.create(
                            change_type=ComparisonChangeType.MODIFIED,
                            object_type=ComparisonObjectType.TABLE,
                            canonical_id=b_tbl.table_id,
                            namespace=b_tbl.namespace,
                            name=b_tbl.name,
                            engine=baseline.payload.engine,
                            before_evidence=before_ev,
                            after_evidence=after_ev,
                            property_differences=sorted_diffs,
                            metadata_completeness=effective_completeness,
                        )
                    )

                # 3. Contained Columns
                col_changes = ColumnComparator.compare_columns(
                    baseline_table=b_tbl,
                    target_table=t_tbl,
                    baseline_snapshot_id=baseline.snapshot_id,
                    target_snapshot_id=target.snapshot_id,
                    engine=baseline.payload.engine,
                    config=config,
                    table_completeness=effective_completeness,
                )
                changes.extend(col_changes)

                # 4. Contained Constraints (PK, FK, Unique, Check)
                con_changes = ConstraintComparator.compare_constraints(
                    baseline_table=b_tbl,
                    target_table=t_tbl,
                    baseline_snapshot_id=baseline.snapshot_id,
                    target_snapshot_id=target.snapshot_id,
                    engine=baseline.payload.engine,
                    config=config,
                    table_completeness=effective_completeness,
                )
                changes.extend(con_changes)

                # 5. Contained Indexes
                idx_changes = IndexComparator.compare_indexes(
                    baseline_table=b_tbl,
                    target_table=t_tbl,
                    baseline_snapshot_id=baseline.snapshot_id,
                    target_snapshot_id=target.snapshot_id,
                    engine=baseline.payload.engine,
                    config=config,
                    table_completeness=effective_completeness,
                )
                changes.extend(idx_changes)

        return changes

    @staticmethod
    def _is_namespace_allowed(namespace: str, config: ComparisonConfig) -> bool:
        if config.included_namespaces and namespace not in config.included_namespaces:
            return False
        if config.excluded_namespaces and namespace in config.excluded_namespaces:
            return False
        return True
