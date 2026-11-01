"""DERA Comparison — Phase 9.1 Index Comparator.

Detects added, removed, and modified indexes:
- Index method (BTREE, HASH, GIN, GIST, etc.)
- Index key columns and ordering
- Uniqueness flag
- Partial index WHERE predicates
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from dera.comparison.enums import (
    ComparisonChangeType,
    ComparisonObjectType,
    PropertyComparisonStatus,
)
from dera.comparison.evidence import ObjectEvidence, PropertyDifference
from dera.comparison.matching import index_canonical_key, match_by_key
from dera.comparison.models import SchemaChange
from dera.comparison.ordering import sort_property_differences
from dera.metadata.enums import MetadataCompleteness
from dera.reverse_engineering.snapshots.models import (
    SnapshotIndexPayload,
    SnapshotTablePayload,
)

if TYPE_CHECKING:
    from dera.comparison.models import ComparisonConfig


class IndexComparator:
    """Compares indexes contained within a table."""

    @staticmethod
    def compare_indexes(
        baseline_table: SnapshotTablePayload,
        target_table: SnapshotTablePayload,
        baseline_snapshot_id: str,
        target_snapshot_id: str,
        engine: str,
        config: ComparisonConfig,
        table_completeness: MetadataCompleteness,
    ) -> list[SchemaChange]:
        """Produce SchemaChange records for all index differences in a table."""
        changes: list[SchemaChange] = []
        matches = match_by_key(
            baseline_items=baseline_table.indexes,
            target_items=target_table.indexes,
            key_fn=index_canonical_key,
        )

        for match in matches:
            if match.is_removed:
                b_idx: SnapshotIndexPayload = match.baseline
                before_ev = ObjectEvidence(
                    snapshot_id=baseline_snapshot_id,
                    object_id=b_idx.index_id,
                    namespace=baseline_table.namespace,
                    name=b_idx.name,
                    properties=b_idx.model_dump(mode="json"),
                    completeness=table_completeness,
                )
                changes.append(
                    SchemaChange.create(
                        change_type=ComparisonChangeType.REMOVED,
                        object_type=ComparisonObjectType.INDEX,
                        canonical_id=b_idx.index_id,
                        namespace=baseline_table.namespace,
                        name=b_idx.name,
                        engine=engine,
                        parent_canonical_id=baseline_table.table_id,
                        parent_name=baseline_table.name,
                        before_evidence=before_ev,
                        after_evidence=None,
                        metadata_completeness=table_completeness,
                    )
                )

            elif match.is_added:
                t_idx: SnapshotIndexPayload = match.target
                after_ev = ObjectEvidence(
                    snapshot_id=target_snapshot_id,
                    object_id=t_idx.index_id,
                    namespace=target_table.namespace,
                    name=t_idx.name,
                    properties=t_idx.model_dump(mode="json"),
                    completeness=table_completeness,
                )
                changes.append(
                    SchemaChange.create(
                        change_type=ComparisonChangeType.ADDED,
                        object_type=ComparisonObjectType.INDEX,
                        canonical_id=t_idx.index_id,
                        namespace=target_table.namespace,
                        name=t_idx.name,
                        engine=engine,
                        parent_canonical_id=target_table.table_id,
                        parent_name=target_table.name,
                        before_evidence=None,
                        after_evidence=after_ev,
                        metadata_completeness=table_completeness,
                    )
                )

            elif match.is_both:
                b_idx = match.baseline
                t_idx = match.target
                prop_diffs: list[PropertyDifference] = []

                if b_idx.columns != t_idx.columns:
                    prop_diffs.append(
                        PropertyDifference(
                            property_name="columns",
                            before_value=list(b_idx.columns),
                            after_value=list(t_idx.columns),
                            status=PropertyComparisonStatus.MODIFIED,
                        )
                    )

                if b_idx.is_unique != t_idx.is_unique:
                    prop_diffs.append(
                        PropertyDifference(
                            property_name="is_unique",
                            before_value=b_idx.is_unique,
                            after_value=t_idx.is_unique,
                            status=PropertyComparisonStatus.MODIFIED,
                        )
                    )

                if b_idx.index_type.upper() != t_idx.index_type.upper():
                    prop_diffs.append(
                        PropertyDifference(
                            property_name="index_type",
                            before_value=b_idx.index_type,
                            after_value=t_idx.index_type,
                            status=PropertyComparisonStatus.MODIFIED,
                            is_engine_specific=True,
                        )
                    )

                b_pred = (b_idx.predicate or "").strip()
                t_pred = (t_idx.predicate or "").strip()
                if b_pred != t_pred:
                    prop_diffs.append(
                        PropertyDifference(
                            property_name="predicate",
                            before_value=b_idx.predicate,
                            after_value=t_idx.predicate,
                            status=PropertyComparisonStatus.MODIFIED,
                        )
                    )

                if prop_diffs:
                    sorted_diffs = sort_property_differences(prop_diffs)
                    before_ev = ObjectEvidence(
                        snapshot_id=baseline_snapshot_id,
                        object_id=b_idx.index_id,
                        namespace=baseline_table.namespace,
                        name=b_idx.name,
                        properties=b_idx.model_dump(mode="json"),
                        completeness=table_completeness,
                    )
                    after_ev = ObjectEvidence(
                        snapshot_id=target_snapshot_id,
                        object_id=t_idx.index_id,
                        namespace=target_table.namespace,
                        name=t_idx.name,
                        properties=t_idx.model_dump(mode="json"),
                        completeness=table_completeness,
                    )
                    changes.append(
                        SchemaChange.create(
                            change_type=ComparisonChangeType.MODIFIED,
                            object_type=ComparisonObjectType.INDEX,
                            canonical_id=b_idx.index_id,
                            namespace=baseline_table.namespace,
                            name=b_idx.name,
                            engine=engine,
                            parent_canonical_id=baseline_table.table_id,
                            parent_name=baseline_table.name,
                            before_evidence=before_ev,
                            after_evidence=after_ev,
                            property_differences=sorted_diffs,
                            metadata_completeness=table_completeness,
                        )
                    )
        return changes
