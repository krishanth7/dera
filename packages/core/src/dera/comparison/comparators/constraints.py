"""DERA Comparison — Phase 9.1 Constraint Comparator.

Detects added, removed, and modified constraints:
- Primary key constraints (membership and column ordering)
- Foreign key constraints (source columns, referenced namespace/table/columns, actions, deferrability)
- Unique constraints (constrained column sequences)
- Check constraints (inert expression comparison)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from dera.comparison.enums import (
    ComparisonChangeType,
    ComparisonObjectType,
    PropertyComparisonStatus,
)
from dera.comparison.evidence import ObjectEvidence, PropertyDifference
from dera.comparison.matching import (
    check_constraint_canonical_key,
    foreign_key_canonical_key,
    match_by_key,
    primary_key_canonical_key,
    unique_constraint_canonical_key,
)
from dera.comparison.models import SchemaChange
from dera.comparison.ordering import sort_property_differences
from dera.metadata.enums import MetadataCompleteness
from dera.reverse_engineering.snapshots.models import (
    SnapshotCheckConstraintPayload,
    SnapshotForeignKeyPayload,
    SnapshotPrimaryKeyPayload,
    SnapshotTablePayload,
    SnapshotUniqueConstraintPayload,
)

if TYPE_CHECKING:
    from dera.comparison.models import ComparisonConfig


class ConstraintComparator:
    """Compares primary keys, foreign keys, unique, and check constraints."""

    @classmethod
    def compare_constraints(
        cls,
        baseline_table: SnapshotTablePayload,
        target_table: SnapshotTablePayload,
        baseline_snapshot_id: str,
        target_snapshot_id: str,
        engine: str,
        config: ComparisonConfig,
        table_completeness: MetadataCompleteness,
    ) -> list[SchemaChange]:
        """Produce SchemaChange records for all constraint differences in a table."""
        changes: list[SchemaChange] = []

        # 1. Primary Keys
        changes.extend(
            cls._compare_primary_keys(
                baseline_table=baseline_table,
                target_table=target_table,
                baseline_snapshot_id=baseline_snapshot_id,
                target_snapshot_id=target_snapshot_id,
                engine=engine,
                table_completeness=table_completeness,
            )
        )

        # 2. Foreign Keys
        changes.extend(
            cls._compare_foreign_keys(
                baseline_table=baseline_table,
                target_table=target_table,
                baseline_snapshot_id=baseline_snapshot_id,
                target_snapshot_id=target_snapshot_id,
                engine=engine,
                table_completeness=table_completeness,
            )
        )

        # 3. Unique Constraints
        changes.extend(
            cls._compare_unique_constraints(
                baseline_table=baseline_table,
                target_table=target_table,
                baseline_snapshot_id=baseline_snapshot_id,
                target_snapshot_id=target_snapshot_id,
                engine=engine,
                table_completeness=table_completeness,
            )
        )

        # 4. Check Constraints
        changes.extend(
            cls._compare_check_constraints(
                baseline_table=baseline_table,
                target_table=target_table,
                baseline_snapshot_id=baseline_snapshot_id,
                target_snapshot_id=target_snapshot_id,
                engine=engine,
                table_completeness=table_completeness,
            )
        )

        return changes

    @staticmethod
    def _compare_primary_keys(
        baseline_table: SnapshotTablePayload,
        target_table: SnapshotTablePayload,
        baseline_snapshot_id: str,
        target_snapshot_id: str,
        engine: str,
        table_completeness: MetadataCompleteness,
    ) -> list[SchemaChange]:
        b_pk = baseline_table.primary_key
        t_pk = target_table.primary_key

        if b_pk is None and t_pk is None:
            return []

        if b_pk is not None and t_pk is None:
            # Removed PK
            before_ev = ObjectEvidence(
                snapshot_id=baseline_snapshot_id,
                object_id=b_pk.constraint_id,
                namespace=baseline_table.namespace,
                name=b_pk.name,
                properties=b_pk.model_dump(mode="json"),
                completeness=table_completeness,
            )
            return [
                SchemaChange.create(
                    change_type=ComparisonChangeType.REMOVED,
                    object_type=ComparisonObjectType.PRIMARY_KEY,
                    canonical_id=b_pk.constraint_id,
                    namespace=baseline_table.namespace,
                    name=b_pk.name,
                    engine=engine,
                    parent_canonical_id=baseline_table.table_id,
                    parent_name=baseline_table.name,
                    before_evidence=before_ev,
                    after_evidence=None,
                    metadata_completeness=table_completeness,
                )
            ]

        if b_pk is None and t_pk is not None:
            # Added PK
            after_ev = ObjectEvidence(
                snapshot_id=target_snapshot_id,
                object_id=t_pk.constraint_id,
                namespace=target_table.namespace,
                name=t_pk.name,
                properties=t_pk.model_dump(mode="json"),
                completeness=table_completeness,
            )
            return [
                SchemaChange.create(
                    change_type=ComparisonChangeType.ADDED,
                    object_type=ComparisonObjectType.PRIMARY_KEY,
                    canonical_id=t_pk.constraint_id,
                    namespace=target_table.namespace,
                    name=t_pk.name,
                    engine=engine,
                    parent_canonical_id=target_table.table_id,
                    parent_name=target_table.name,
                    before_evidence=None,
                    after_evidence=after_ev,
                    metadata_completeness=table_completeness,
                )
            ]

        # Both present: check columns and column ordering
        prop_diffs: list[PropertyDifference] = []
        if b_pk.columns != t_pk.columns:
            prop_diffs.append(
                PropertyDifference(
                    property_name="columns",
                    before_value=list(b_pk.columns),
                    after_value=list(t_pk.columns),
                    status=PropertyComparisonStatus.MODIFIED,
                )
            )

        if prop_diffs:
            sorted_diffs = sort_property_differences(prop_diffs)
            before_ev = ObjectEvidence(
                snapshot_id=baseline_snapshot_id,
                object_id=b_pk.constraint_id,
                namespace=baseline_table.namespace,
                name=b_pk.name,
                properties=b_pk.model_dump(mode="json"),
                completeness=table_completeness,
            )
            after_ev = ObjectEvidence(
                snapshot_id=target_snapshot_id,
                object_id=t_pk.constraint_id,
                namespace=target_table.namespace,
                name=t_pk.name,
                properties=t_pk.model_dump(mode="json"),
                completeness=table_completeness,
            )
            return [
                SchemaChange.create(
                    change_type=ComparisonChangeType.MODIFIED,
                    object_type=ComparisonObjectType.PRIMARY_KEY,
                    canonical_id=b_pk.constraint_id,
                    namespace=baseline_table.namespace,
                    name=b_pk.name,
                    engine=engine,
                    parent_canonical_id=baseline_table.table_id,
                    parent_name=baseline_table.name,
                    before_evidence=before_ev,
                    after_evidence=after_ev,
                    property_differences=sorted_diffs,
                    metadata_completeness=table_completeness,
                )
            ]
        return []

    @staticmethod
    def _compare_foreign_keys(
        baseline_table: SnapshotTablePayload,
        target_table: SnapshotTablePayload,
        baseline_snapshot_id: str,
        target_snapshot_id: str,
        engine: str,
        table_completeness: MetadataCompleteness,
    ) -> list[SchemaChange]:
        changes: list[SchemaChange] = []
        matches = match_by_key(
            baseline_items=baseline_table.foreign_keys,
            target_items=target_table.foreign_keys,
            key_fn=foreign_key_canonical_key,
        )

        for match in matches:
            if match.is_removed:
                b_fk: SnapshotForeignKeyPayload = match.baseline
                before_ev = ObjectEvidence(
                    snapshot_id=baseline_snapshot_id,
                    object_id=b_fk.constraint_id,
                    namespace=baseline_table.namespace,
                    name=b_fk.name,
                    properties=b_fk.model_dump(mode="json"),
                    completeness=table_completeness,
                )
                changes.append(
                    SchemaChange.create(
                        change_type=ComparisonChangeType.REMOVED,
                        object_type=ComparisonObjectType.FOREIGN_KEY,
                        canonical_id=b_fk.constraint_id,
                        namespace=baseline_table.namespace,
                        name=b_fk.name,
                        engine=engine,
                        parent_canonical_id=baseline_table.table_id,
                        parent_name=baseline_table.name,
                        before_evidence=before_ev,
                        after_evidence=None,
                        metadata_completeness=table_completeness,
                    )
                )
            elif match.is_added:
                t_fk: SnapshotForeignKeyPayload = match.target
                after_ev = ObjectEvidence(
                    snapshot_id=target_snapshot_id,
                    object_id=t_fk.constraint_id,
                    namespace=target_table.namespace,
                    name=t_fk.name,
                    properties=t_fk.model_dump(mode="json"),
                    completeness=table_completeness,
                )
                changes.append(
                    SchemaChange.create(
                        change_type=ComparisonChangeType.ADDED,
                        object_type=ComparisonObjectType.FOREIGN_KEY,
                        canonical_id=t_fk.constraint_id,
                        namespace=target_table.namespace,
                        name=t_fk.name,
                        engine=engine,
                        parent_canonical_id=target_table.table_id,
                        parent_name=target_table.name,
                        before_evidence=None,
                        after_evidence=after_ev,
                        metadata_completeness=table_completeness,
                    )
                )
            elif match.is_both:
                b_fk = match.baseline
                t_fk = match.target
                prop_diffs: list[PropertyDifference] = []

                if b_fk.source_columns != t_fk.source_columns:
                    prop_diffs.append(
                        PropertyDifference(
                            property_name="source_columns",
                            before_value=list(b_fk.source_columns),
                            after_value=list(t_fk.source_columns),
                            status=PropertyComparisonStatus.MODIFIED,
                        )
                    )

                if b_fk.target_table != t_fk.target_table:
                    prop_diffs.append(
                        PropertyDifference(
                            property_name="target_table",
                            before_value=b_fk.target_table,
                            after_value=t_fk.target_table,
                            status=PropertyComparisonStatus.MODIFIED,
                        )
                    )

                if b_fk.target_namespace != t_fk.target_namespace:
                    prop_diffs.append(
                        PropertyDifference(
                            property_name="target_namespace",
                            before_value=b_fk.target_namespace,
                            after_value=t_fk.target_namespace,
                            status=PropertyComparisonStatus.MODIFIED,
                        )
                    )

                if b_fk.target_columns != t_fk.target_columns:
                    prop_diffs.append(
                        PropertyDifference(
                            property_name="target_columns",
                            before_value=list(b_fk.target_columns),
                            after_value=list(t_fk.target_columns),
                            status=PropertyComparisonStatus.MODIFIED,
                        )
                    )

                if b_fk.on_update != t_fk.on_update:
                    prop_diffs.append(
                        PropertyDifference(
                            property_name="on_update",
                            before_value=b_fk.on_update.value,
                            after_value=t_fk.on_update.value,
                            status=PropertyComparisonStatus.MODIFIED,
                        )
                    )

                if b_fk.on_delete != t_fk.on_delete:
                    prop_diffs.append(
                        PropertyDifference(
                            property_name="on_delete",
                            before_value=b_fk.on_delete.value,
                            after_value=t_fk.on_delete.value,
                            status=PropertyComparisonStatus.MODIFIED,
                        )
                    )

                if b_fk.is_deferrable != t_fk.is_deferrable:
                    prop_diffs.append(
                        PropertyDifference(
                            property_name="is_deferrable",
                            before_value=b_fk.is_deferrable,
                            after_value=t_fk.is_deferrable,
                            status=PropertyComparisonStatus.MODIFIED,
                        )
                    )

                if prop_diffs:
                    sorted_diffs = sort_property_differences(prop_diffs)
                    before_ev = ObjectEvidence(
                        snapshot_id=baseline_snapshot_id,
                        object_id=b_fk.constraint_id,
                        namespace=baseline_table.namespace,
                        name=b_fk.name,
                        properties=b_fk.model_dump(mode="json"),
                        completeness=table_completeness,
                    )
                    after_ev = ObjectEvidence(
                        snapshot_id=target_snapshot_id,
                        object_id=t_fk.constraint_id,
                        namespace=target_table.namespace,
                        name=t_fk.name,
                        properties=t_fk.model_dump(mode="json"),
                        completeness=table_completeness,
                    )
                    changes.append(
                        SchemaChange.create(
                            change_type=ComparisonChangeType.MODIFIED,
                            object_type=ComparisonObjectType.FOREIGN_KEY,
                            canonical_id=b_fk.constraint_id,
                            namespace=baseline_table.namespace,
                            name=b_fk.name,
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

    @staticmethod
    def _compare_unique_constraints(
        baseline_table: SnapshotTablePayload,
        target_table: SnapshotTablePayload,
        baseline_snapshot_id: str,
        target_snapshot_id: str,
        engine: str,
        table_completeness: MetadataCompleteness,
    ) -> list[SchemaChange]:
        changes: list[SchemaChange] = []
        matches = match_by_key(
            baseline_items=baseline_table.unique_constraints,
            target_items=target_table.unique_constraints,
            key_fn=unique_constraint_canonical_key,
        )

        for match in matches:
            if match.is_removed:
                b_uc: SnapshotUniqueConstraintPayload = match.baseline
                before_ev = ObjectEvidence(
                    snapshot_id=baseline_snapshot_id,
                    object_id=b_uc.constraint_id,
                    namespace=baseline_table.namespace,
                    name=b_uc.name,
                    properties=b_uc.model_dump(mode="json"),
                    completeness=table_completeness,
                )
                changes.append(
                    SchemaChange.create(
                        change_type=ComparisonChangeType.REMOVED,
                        object_type=ComparisonObjectType.UNIQUE_CONSTRAINT,
                        canonical_id=b_uc.constraint_id,
                        namespace=baseline_table.namespace,
                        name=b_uc.name,
                        engine=engine,
                        parent_canonical_id=baseline_table.table_id,
                        parent_name=baseline_table.name,
                        before_evidence=before_ev,
                        after_evidence=None,
                        metadata_completeness=table_completeness,
                    )
                )
            elif match.is_added:
                t_uc: SnapshotUniqueConstraintPayload = match.target
                after_ev = ObjectEvidence(
                    snapshot_id=target_snapshot_id,
                    object_id=t_uc.constraint_id,
                    namespace=target_table.namespace,
                    name=t_uc.name,
                    properties=t_uc.model_dump(mode="json"),
                    completeness=table_completeness,
                )
                changes.append(
                    SchemaChange.create(
                        change_type=ComparisonChangeType.ADDED,
                        object_type=ComparisonObjectType.UNIQUE_CONSTRAINT,
                        canonical_id=t_uc.constraint_id,
                        namespace=target_table.namespace,
                        name=t_uc.name,
                        engine=engine,
                        parent_canonical_id=target_table.table_id,
                        parent_name=target_table.name,
                        before_evidence=None,
                        after_evidence=after_ev,
                        metadata_completeness=table_completeness,
                    )
                )
            elif match.is_both:
                b_uc = match.baseline
                t_uc = match.target
                prop_diffs: list[PropertyDifference] = []

                if b_uc.columns != t_uc.columns:
                    prop_diffs.append(
                        PropertyDifference(
                            property_name="columns",
                            before_value=list(b_uc.columns),
                            after_value=list(t_uc.columns),
                            status=PropertyComparisonStatus.MODIFIED,
                        )
                    )

                if prop_diffs:
                    sorted_diffs = sort_property_differences(prop_diffs)
                    before_ev = ObjectEvidence(
                        snapshot_id=baseline_snapshot_id,
                        object_id=b_uc.constraint_id,
                        namespace=baseline_table.namespace,
                        name=b_uc.name,
                        properties=b_uc.model_dump(mode="json"),
                        completeness=table_completeness,
                    )
                    after_ev = ObjectEvidence(
                        snapshot_id=target_snapshot_id,
                        object_id=t_uc.constraint_id,
                        namespace=target_table.namespace,
                        name=t_uc.name,
                        properties=t_uc.model_dump(mode="json"),
                        completeness=table_completeness,
                    )
                    changes.append(
                        SchemaChange.create(
                            change_type=ComparisonChangeType.MODIFIED,
                            object_type=ComparisonObjectType.UNIQUE_CONSTRAINT,
                            canonical_id=b_uc.constraint_id,
                            namespace=baseline_table.namespace,
                            name=b_uc.name,
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

    @staticmethod
    def _compare_check_constraints(
        baseline_table: SnapshotTablePayload,
        target_table: SnapshotTablePayload,
        baseline_snapshot_id: str,
        target_snapshot_id: str,
        engine: str,
        table_completeness: MetadataCompleteness,
    ) -> list[SchemaChange]:
        changes: list[SchemaChange] = []
        matches = match_by_key(
            baseline_items=baseline_table.check_constraints,
            target_items=target_table.check_constraints,
            key_fn=check_constraint_canonical_key,
        )

        for match in matches:
            if match.is_removed:
                b_chk: SnapshotCheckConstraintPayload = match.baseline
                before_ev = ObjectEvidence(
                    snapshot_id=baseline_snapshot_id,
                    object_id=b_chk.constraint_id,
                    namespace=baseline_table.namespace,
                    name=b_chk.name,
                    properties=b_chk.model_dump(mode="json"),
                    completeness=table_completeness,
                )
                changes.append(
                    SchemaChange.create(
                        change_type=ComparisonChangeType.REMOVED,
                        object_type=ComparisonObjectType.CHECK_CONSTRAINT,
                        canonical_id=b_chk.constraint_id,
                        namespace=baseline_table.namespace,
                        name=b_chk.name,
                        engine=engine,
                        parent_canonical_id=baseline_table.table_id,
                        parent_name=baseline_table.name,
                        before_evidence=before_ev,
                        after_evidence=None,
                        metadata_completeness=table_completeness,
                    )
                )
            elif match.is_added:
                t_chk: SnapshotCheckConstraintPayload = match.target
                after_ev = ObjectEvidence(
                    snapshot_id=target_snapshot_id,
                    object_id=t_chk.constraint_id,
                    namespace=target_table.namespace,
                    name=t_chk.name,
                    properties=t_chk.model_dump(mode="json"),
                    completeness=table_completeness,
                )
                changes.append(
                    SchemaChange.create(
                        change_type=ComparisonChangeType.ADDED,
                        object_type=ComparisonObjectType.CHECK_CONSTRAINT,
                        canonical_id=t_chk.constraint_id,
                        namespace=target_table.namespace,
                        name=t_chk.name,
                        engine=engine,
                        parent_canonical_id=target_table.table_id,
                        parent_name=target_table.name,
                        before_evidence=None,
                        after_evidence=after_ev,
                        metadata_completeness=table_completeness,
                    )
                )
            elif match.is_both:
                b_chk = match.baseline
                t_chk = match.target
                prop_diffs: list[PropertyDifference] = []

                if b_chk.expression.strip() != t_chk.expression.strip():
                    prop_diffs.append(
                        PropertyDifference(
                            property_name="expression",
                            before_value=b_chk.expression,
                            after_value=t_chk.expression,
                            status=PropertyComparisonStatus.MODIFIED,
                        )
                    )

                if prop_diffs:
                    sorted_diffs = sort_property_differences(prop_diffs)
                    before_ev = ObjectEvidence(
                        snapshot_id=baseline_snapshot_id,
                        object_id=b_chk.constraint_id,
                        namespace=baseline_table.namespace,
                        name=b_chk.name,
                        properties=b_chk.model_dump(mode="json"),
                        completeness=table_completeness,
                    )
                    after_ev = ObjectEvidence(
                        snapshot_id=target_snapshot_id,
                        object_id=t_chk.constraint_id,
                        namespace=target_table.namespace,
                        name=t_chk.name,
                        properties=t_chk.model_dump(mode="json"),
                        completeness=table_completeness,
                    )
                    changes.append(
                        SchemaChange.create(
                            change_type=ComparisonChangeType.MODIFIED,
                            object_type=ComparisonObjectType.CHECK_CONSTRAINT,
                            canonical_id=b_chk.constraint_id,
                            namespace=baseline_table.namespace,
                            name=b_chk.name,
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
