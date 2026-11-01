"""DERA Comparison — Phase 9.1 Column Comparator.

Detects added, removed, and modified table columns with precise property-level evidence:
- Data type changes
- Nullability transitions (nullable <-> non-nullable)
- Default expression changes
- Ordinal position / column ordering
- Character maximum length, precision, scale
- Column comments (if not ignored)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from dera.comparison.enums import (
    ComparisonChangeType,
    ComparisonObjectType,
    PropertyComparisonStatus,
)
from dera.comparison.evidence import ObjectEvidence, PropertyDifference
from dera.comparison.matching import column_canonical_key, match_by_key
from dera.comparison.models import SchemaChange
from dera.comparison.ordering import sort_property_differences
from dera.metadata.enums import MetadataCompleteness
from dera.reverse_engineering.snapshots.models import (
    SnapshotColumnPayload,
    SnapshotTablePayload,
)

if TYPE_CHECKING:
    from dera.comparison.models import ComparisonConfig


class ColumnComparator:
    """Compares columns contained within a table."""

    @staticmethod
    def compare_columns(
        baseline_table: SnapshotTablePayload,
        target_table: SnapshotTablePayload,
        baseline_snapshot_id: str,
        target_snapshot_id: str,
        engine: str,
        config: ComparisonConfig,
        table_completeness: MetadataCompleteness,
    ) -> list[SchemaChange]:
        """Produce SchemaChange records for column differences within a matched table."""
        changes: list[SchemaChange] = []

        matches = match_by_key(
            baseline_items=baseline_table.columns,
            target_items=target_table.columns,
            key_fn=column_canonical_key,
        )

        for match in matches:
            if match.is_removed:
                b_col: SnapshotColumnPayload = match.baseline
                b_props = b_col.model_dump(mode="json")
                before_ev = ObjectEvidence(
                    snapshot_id=baseline_snapshot_id,
                    object_id=b_col.column_id,
                    namespace=baseline_table.namespace,
                    name=b_col.name,
                    properties=b_props,
                    completeness=table_completeness,
                )
                changes.append(
                    SchemaChange.create(
                        change_type=ComparisonChangeType.REMOVED,
                        object_type=ComparisonObjectType.COLUMN,
                        canonical_id=b_col.column_id,
                        namespace=baseline_table.namespace,
                        name=b_col.name,
                        engine=engine,
                        parent_canonical_id=baseline_table.table_id,
                        parent_name=baseline_table.name,
                        before_evidence=before_ev,
                        after_evidence=None,
                        metadata_completeness=table_completeness,
                    )
                )

            elif match.is_added:
                t_col: SnapshotColumnPayload = match.target
                t_props = t_col.model_dump(mode="json")
                after_ev = ObjectEvidence(
                    snapshot_id=target_snapshot_id,
                    object_id=t_col.column_id,
                    namespace=target_table.namespace,
                    name=t_col.name,
                    properties=t_props,
                    completeness=table_completeness,
                )
                changes.append(
                    SchemaChange.create(
                        change_type=ComparisonChangeType.ADDED,
                        object_type=ComparisonObjectType.COLUMN,
                        canonical_id=t_col.column_id,
                        namespace=target_table.namespace,
                        name=t_col.name,
                        engine=engine,
                        parent_canonical_id=target_table.table_id,
                        parent_name=target_table.name,
                        before_evidence=None,
                        after_evidence=after_ev,
                        metadata_completeness=table_completeness,
                    )
                )

            elif match.is_both:
                b_col = match.baseline
                t_col = match.target
                prop_diffs: list[PropertyDifference] = []

                # 1. Native data type
                if b_col.native_data_type != t_col.native_data_type:
                    prop_diffs.append(
                        PropertyDifference(
                            property_name="native_data_type",
                            before_value=b_col.native_data_type,
                            after_value=t_col.native_data_type,
                            status=PropertyComparisonStatus.MODIFIED,
                            is_engine_specific=True,
                        )
                    )

                # 2. Canonical type
                if b_col.canonical_type != t_col.canonical_type:
                    prop_diffs.append(
                        PropertyDifference(
                            property_name="canonical_type",
                            before_value=b_col.canonical_type.value,
                            after_value=t_col.canonical_type.value,
                            status=PropertyComparisonStatus.MODIFIED,
                        )
                    )

                # 3. Nullability
                if b_col.is_nullable != t_col.is_nullable:
                    prop_diffs.append(
                        PropertyDifference(
                            property_name="is_nullable",
                            before_value=b_col.is_nullable,
                            after_value=t_col.is_nullable,
                            status=PropertyComparisonStatus.MODIFIED,
                        )
                    )

                # 4. Default expression
                if b_col.default_expression != t_col.default_expression:
                    prop_diffs.append(
                        PropertyDifference(
                            property_name="default_expression",
                            before_value=b_col.default_expression,
                            after_value=t_col.default_expression,
                            status=PropertyComparisonStatus.MODIFIED,
                        )
                    )

                # 5. Ordinal position (unless ignored by config)
                if not config.ignore_column_order:
                    if b_col.ordinal_position != t_col.ordinal_position:
                        prop_diffs.append(
                            PropertyDifference(
                                property_name="ordinal_position",
                                before_value=b_col.ordinal_position,
                                after_value=t_col.ordinal_position,
                                status=PropertyComparisonStatus.MODIFIED,
                            )
                        )

                # 6. Maximum length, precision, scale
                if b_col.character_maximum_length != t_col.character_maximum_length:
                    prop_diffs.append(
                        PropertyDifference(
                            property_name="character_maximum_length",
                            before_value=b_col.character_maximum_length,
                            after_value=t_col.character_maximum_length,
                            status=PropertyComparisonStatus.MODIFIED,
                        )
                    )

                if b_col.numeric_precision != t_col.numeric_precision:
                    prop_diffs.append(
                        PropertyDifference(
                            property_name="numeric_precision",
                            before_value=b_col.numeric_precision,
                            after_value=t_col.numeric_precision,
                            status=PropertyComparisonStatus.MODIFIED,
                        )
                    )

                if b_col.numeric_scale != t_col.numeric_scale:
                    prop_diffs.append(
                        PropertyDifference(
                            property_name="numeric_scale",
                            before_value=b_col.numeric_scale,
                            after_value=t_col.numeric_scale,
                            status=PropertyComparisonStatus.MODIFIED,
                        )
                    )

                # 7. Comments
                if not config.ignore_comments:
                    if b_col.comment != t_col.comment:
                        prop_diffs.append(
                            PropertyDifference(
                                property_name="comment",
                                before_value=b_col.comment,
                                after_value=t_col.comment,
                                status=PropertyComparisonStatus.MODIFIED,
                            )
                        )

                if prop_diffs:
                    sorted_diffs = sort_property_differences(prop_diffs)
                    before_ev = ObjectEvidence(
                        snapshot_id=baseline_snapshot_id,
                        object_id=b_col.column_id,
                        namespace=baseline_table.namespace,
                        name=b_col.name,
                        properties=b_col.model_dump(mode="json"),
                        completeness=table_completeness,
                    )
                    after_ev = ObjectEvidence(
                        snapshot_id=target_snapshot_id,
                        object_id=t_col.column_id,
                        namespace=target_table.namespace,
                        name=t_col.name,
                        properties=t_col.model_dump(mode="json"),
                        completeness=table_completeness,
                    )
                    changes.append(
                        SchemaChange.create(
                            change_type=ComparisonChangeType.MODIFIED,
                            object_type=ComparisonObjectType.COLUMN,
                            canonical_id=b_col.column_id,
                            namespace=baseline_table.namespace,
                            name=b_col.name,
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
