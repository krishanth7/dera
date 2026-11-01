"""DERA Comparison — Phase 9.1 View Comparator.

Detects added, removed, and modified database views:
- View existence
- View SQL definition changes
- Materialized view flag changes
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from dera.comparison.enums import (
    ComparisonChangeType,
    ComparisonObjectType,
    PropertyComparisonStatus,
)
from dera.comparison.evidence import ObjectEvidence, PropertyDifference
from dera.comparison.matching import match_by_key, view_canonical_key
from dera.comparison.models import SchemaChange
from dera.comparison.ordering import sort_property_differences
from dera.metadata.enums import MetadataCompleteness
from dera.reverse_engineering.snapshots.models import SnapshotViewPayload

if TYPE_CHECKING:
    from dera.comparison.models import ComparisonConfig
    from dera.reverse_engineering.snapshots.models import SchemaSnapshot


class ViewComparator:
    """Compares views across schema snapshots."""

    @classmethod
    def compare_views(
        cls,
        baseline: SchemaSnapshot,
        target: SchemaSnapshot,
        config: ComparisonConfig,
    ) -> list[SchemaChange]:
        """Produce SchemaChange records for view differences."""
        changes: list[SchemaChange] = []

        b_views = [
            v for v in baseline.payload.views if cls._is_namespace_allowed(v.namespace, config)
        ]
        t_views = [
            v for v in target.payload.views if cls._is_namespace_allowed(v.namespace, config)
        ]

        matches = match_by_key(
            baseline_items=b_views,
            target_items=t_views,
            key_fn=view_canonical_key,
        )

        for match in matches:
            if match.is_removed:
                b_vw: SnapshotViewPayload = match.baseline
                before_ev = ObjectEvidence(
                    snapshot_id=baseline.snapshot_id,
                    object_id=b_vw.view_id,
                    namespace=b_vw.namespace,
                    name=b_vw.name,
                    properties=b_vw.model_dump(mode="json"),
                    completeness=baseline.payload.completeness,
                )
                changes.append(
                    SchemaChange.create(
                        change_type=ComparisonChangeType.REMOVED,
                        object_type=ComparisonObjectType.VIEW,
                        canonical_id=b_vw.view_id,
                        namespace=b_vw.namespace,
                        name=b_vw.name,
                        engine=baseline.payload.engine,
                        before_evidence=before_ev,
                        after_evidence=None,
                        metadata_completeness=baseline.payload.completeness,
                    )
                )

            elif match.is_added:
                t_vw: SnapshotViewPayload = match.target
                after_ev = ObjectEvidence(
                    snapshot_id=target.snapshot_id,
                    object_id=t_vw.view_id,
                    namespace=t_vw.namespace,
                    name=t_vw.name,
                    properties=t_vw.model_dump(mode="json"),
                    completeness=target.payload.completeness,
                )
                changes.append(
                    SchemaChange.create(
                        change_type=ComparisonChangeType.ADDED,
                        object_type=ComparisonObjectType.VIEW,
                        canonical_id=t_vw.view_id,
                        namespace=t_vw.namespace,
                        name=t_vw.name,
                        engine=target.payload.engine,
                        before_evidence=None,
                        after_evidence=after_ev,
                        metadata_completeness=target.payload.completeness,
                    )
                )

            elif match.is_both:
                b_vw = match.baseline
                t_vw = match.target
                prop_diffs: list[PropertyDifference] = []

                # Definition comparison
                b_def = (b_vw.definition or "").strip()
                t_def = (t_vw.definition or "").strip()
                if b_def != t_def:
                    prop_diffs.append(
                        PropertyDifference(
                            property_name="definition",
                            before_value=b_vw.definition,
                            after_value=t_vw.definition,
                            status=PropertyComparisonStatus.MODIFIED,
                        )
                    )

                # Materialized flag
                if b_vw.is_materialized != t_vw.is_materialized:
                    prop_diffs.append(
                        PropertyDifference(
                            property_name="is_materialized",
                            before_value=b_vw.is_materialized,
                            after_value=t_vw.is_materialized,
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
                        object_id=b_vw.view_id,
                        namespace=b_vw.namespace,
                        name=b_vw.name,
                        properties=b_vw.model_dump(mode="json"),
                        completeness=baseline.payload.completeness,
                    )
                    after_ev = ObjectEvidence(
                        snapshot_id=target.snapshot_id,
                        object_id=t_vw.view_id,
                        namespace=t_vw.namespace,
                        name=t_vw.name,
                        properties=t_vw.model_dump(mode="json"),
                        completeness=target.payload.completeness,
                    )
                    changes.append(
                        SchemaChange.create(
                            change_type=ComparisonChangeType.MODIFIED,
                            object_type=ComparisonObjectType.VIEW,
                            canonical_id=b_vw.view_id,
                            namespace=b_vw.namespace,
                            name=b_vw.name,
                            engine=baseline.payload.engine,
                            before_evidence=before_ev,
                            after_evidence=after_ev,
                            property_differences=sorted_diffs,
                            metadata_completeness=effective_completeness,
                        )
                    )

        return changes

    @staticmethod
    def _is_namespace_allowed(namespace: str, config: ComparisonConfig) -> bool:
        if config.included_namespaces and namespace not in config.included_namespaces:
            return False
        if config.excluded_namespaces and namespace in config.excluded_namespaces:
            return False
        return True
