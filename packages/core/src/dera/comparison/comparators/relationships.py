"""DERA Comparison — Phase 9.1 Relationship Comparator.

Detects added, removed, and modified foreign-key relationship graph edges.
Preserves graph edge direction: referencing child table -> referenced parent table.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from dera.comparison.enums import (
    ComparisonChangeType,
    ComparisonObjectType,
    PropertyComparisonStatus,
)
from dera.comparison.evidence import ObjectEvidence, PropertyDifference
from dera.comparison.matching import match_by_key, relationship_canonical_key
from dera.comparison.models import SchemaChange
from dera.comparison.ordering import sort_property_differences
from dera.metadata.enums import MetadataCompleteness
from dera.reverse_engineering.snapshots.models import (
    SnapshotRelationshipPayload,
)

if TYPE_CHECKING:
    from dera.comparison.models import ComparisonConfig
    from dera.reverse_engineering.snapshots.models import SchemaSnapshot


class RelationshipComparator:
    """Compares foreign key relationship edges across schema snapshots."""

    @classmethod
    def compare_relationships(
        cls,
        baseline: SchemaSnapshot,
        target: SchemaSnapshot,
        config: ComparisonConfig,
    ) -> list[SchemaChange]:
        """Produce SchemaChange records for relationship edge differences."""
        changes: list[SchemaChange] = []

        b_rels = list(baseline.payload.relationships)
        t_rels = list(target.payload.relationships)

        matches = match_by_key(
            baseline_items=b_rels,
            target_items=t_rels,
            key_fn=relationship_canonical_key,
        )

        for match in matches:
            if match.is_removed:
                b_rel: SnapshotRelationshipPayload = match.baseline
                before_ev = ObjectEvidence(
                    snapshot_id=baseline.snapshot_id,
                    object_id=b_rel.edge_id,
                    namespace="",
                    name=b_rel.constraint_name,
                    properties=b_rel.model_dump(mode="json"),
                    completeness=baseline.payload.completeness,
                )
                changes.append(
                    SchemaChange.create(
                        change_type=ComparisonChangeType.REMOVED,
                        object_type=ComparisonObjectType.RELATIONSHIP,
                        canonical_id=b_rel.edge_id,
                        namespace="",
                        name=b_rel.constraint_name,
                        engine=baseline.payload.engine,
                        parent_canonical_id=b_rel.source_table_id,
                        before_evidence=before_ev,
                        after_evidence=None,
                        metadata_completeness=baseline.payload.completeness,
                    )
                )

            elif match.is_added:
                t_rel: SnapshotRelationshipPayload = match.target
                after_ev = ObjectEvidence(
                    snapshot_id=target.snapshot_id,
                    object_id=t_rel.edge_id,
                    namespace="",
                    name=t_rel.constraint_name,
                    properties=t_rel.model_dump(mode="json"),
                    completeness=target.payload.completeness,
                )
                changes.append(
                    SchemaChange.create(
                        change_type=ComparisonChangeType.ADDED,
                        object_type=ComparisonObjectType.RELATIONSHIP,
                        canonical_id=t_rel.edge_id,
                        namespace="",
                        name=t_rel.constraint_name,
                        engine=target.payload.engine,
                        parent_canonical_id=t_rel.source_table_id,
                        before_evidence=None,
                        after_evidence=after_ev,
                        metadata_completeness=target.payload.completeness,
                    )
                )

            elif match.is_both:
                b_rel = match.baseline
                t_rel = match.target
                prop_diffs: list[PropertyDifference] = []

                if b_rel.source_columns != t_rel.source_columns:
                    prop_diffs.append(
                        PropertyDifference(
                            property_name="source_columns",
                            before_value=list(b_rel.source_columns),
                            after_value=list(t_rel.source_columns),
                            status=PropertyComparisonStatus.MODIFIED,
                        )
                    )

                if b_rel.target_columns != t_rel.target_columns:
                    prop_diffs.append(
                        PropertyDifference(
                            property_name="target_columns",
                            before_value=list(b_rel.target_columns),
                            after_value=list(t_rel.target_columns),
                            status=PropertyComparisonStatus.MODIFIED,
                        )
                    )

                if b_rel.target_table_id != t_rel.target_table_id:
                    prop_diffs.append(
                        PropertyDifference(
                            property_name="target_table_id",
                            before_value=b_rel.target_table_id,
                            after_value=t_rel.target_table_id,
                            status=PropertyComparisonStatus.MODIFIED,
                        )
                    )

                if prop_diffs:
                    sorted_diffs = sort_property_differences(prop_diffs)
                    effective_completeness = (
                        MetadataCompleteness.COMPLETE
                        if baseline.payload.completeness == MetadataCompleteness.COMPLETE
                        and target.payload.completeness == MetadataCompleteness.COMPLETE
                        else MetadataCompleteness.PARTIAL
                    )
                    before_ev = ObjectEvidence(
                        snapshot_id=baseline.snapshot_id,
                        object_id=b_rel.edge_id,
                        namespace="",
                        name=b_rel.constraint_name,
                        properties=b_rel.model_dump(mode="json"),
                        completeness=baseline.payload.completeness,
                    )
                    after_ev = ObjectEvidence(
                        snapshot_id=target.snapshot_id,
                        object_id=t_rel.edge_id,
                        namespace="",
                        name=t_rel.constraint_name,
                        properties=t_rel.model_dump(mode="json"),
                        completeness=target.payload.completeness,
                    )
                    changes.append(
                        SchemaChange.create(
                            change_type=ComparisonChangeType.MODIFIED,
                            object_type=ComparisonObjectType.RELATIONSHIP,
                            canonical_id=b_rel.edge_id,
                            namespace="",
                            name=b_rel.constraint_name,
                            engine=baseline.payload.engine,
                            parent_canonical_id=b_rel.source_table_id,
                            before_evidence=before_ev,
                            after_evidence=after_ev,
                            property_differences=sorted_diffs,
                            metadata_completeness=effective_completeness,
                        )
                    )

        return changes
