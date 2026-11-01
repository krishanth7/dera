"""Change to Migration Operation Mapper.

Deterministically transforms Phase 9.1 SchemaChange and Phase 9.2 ClassifiedChange / MigrationRiskAssessment
instances into AbstractMigrationOperation models with verified preconditions,
postconditions, manual decision gates, and rollback considerations.
"""

from dera.comparison.enums import ComparisonChangeType, ComparisonObjectType
from dera.comparison.models import SchemaChange
from dera.migration.classification.models import ClassifiedChange
from dera.migration.enums import ReversibilityClassification, ReviewPriority
from dera.migration.planning.enums import (
    EngineCapabilityState,
    ManualGateStatus,
    MigrationOperationType,
)
from dera.migration.planning.models import (
    AbstractMigrationOperation,
    ManualDecisionGate,
    OperationPostcondition,
    OperationPrecondition,
    RollbackConsideration,
    ValidationRequirement,
)
from dera.migration.planning.operation_catalog import OperationCatalog
from dera.migration.risk.models import MigrationRiskAssessment


class ChangeToOperationMapper:
    """Deterministic mapper converting schema changes into abstract migration operations."""

    def __init__(self, target_engine: str = "postgresql"):
        self.target_engine = target_engine.lower()

    def map_changes(
        self,
        schema_changes: tuple[SchemaChange, ...] | list[SchemaChange],
        classified_changes: tuple[ClassifiedChange, ...] | list[ClassifiedChange] | None = None,
        risk_assessments: tuple[MigrationRiskAssessment, ...]
        | list[MigrationRiskAssessment]
        | None = None,
    ) -> list[AbstractMigrationOperation]:
        """Map all changes into abstract migration operations."""
        classified_map: dict[str, ClassifiedChange] = {}
        if classified_changes:
            for cc in classified_changes:
                classified_map[cc.source_fingerprint] = cc

        risk_map: dict[str, list[MigrationRiskAssessment]] = {}
        if risk_assessments:
            for ra in risk_assessments:
                risk_map.setdefault(ra.source_change_fingerprint, []).append(ra)

        operations: list[AbstractMigrationOperation] = []
        for change in sorted(schema_changes, key=lambda c: c.fingerprint):
            classified = classified_map.get(change.fingerprint)
            risks = risk_map.get(change.fingerprint, [])
            ops = self._map_single_change(change, classified, risks)
            operations.extend(ops)

        return operations

    def _map_single_change(
        self,
        change: SchemaChange,
        classified: ClassifiedChange | None = None,
        risks: list[MigrationRiskAssessment] | None = None,
    ) -> list[AbstractMigrationOperation]:
        """Convert a single schema change to one or more operations."""
        op_type = self._resolve_operation_type(change)
        if op_type is None:
            return []

        op_id = f"op_{op_type.value.lower()}_{change.canonical_id}"
        table_name = (
            change.parent_name
            if change.parent_name
            else (change.name if change.object_type == ComparisonObjectType.TABLE else None)
        )
        namespace = change.namespace or "public"

        entry = OperationCatalog.get_entry(op_type)
        engine_cap = OperationCatalog.get_engine_capability(op_type, self.target_engine)
        engine_limits = OperationCatalog.get_engine_limitations(op_type, self.target_engine)

        # Preconditions
        preconditions = self._build_preconditions(change, op_type, entry)

        # Build diff details dict
        diff_props = {
            d.property_name: {
                "before": d.before_value,
                "after": d.after_value,
            }
            for d in change.property_differences
        }

        # Postconditions
        postconditions = [
            OperationPostcondition(
                postcondition_id=f"post_{op_id}",
                description=f"Verify {change.name} matches target structural state.",
                target_object_id=change.canonical_id,
                expected_state=diff_props,
                verification_method="CANONICAL_METADATA_INSPECTION",
            )
        ]

        # Validation requirements
        validation_reqs = [
            ValidationRequirement(
                requirement_id=f"val_{op_id}",
                operation_id=op_id,
                description=f"Validate {op_type.value} on {change.name}",
                target_object_id=change.canonical_id,
                check_type=f"VERIFY_{op_type.value}",
                expected_metadata=diff_props,
                limitations=[],
            )
        ]

        # Destructive & reversibility analysis
        # Check risks first for reversibility if available
        highest_reversibility = ReversibilityClassification.POTENTIALLY_REVERSIBLE
        highest_priority = ReviewPriority.P4_LOW
        is_destructive = change.change_type == ComparisonChangeType.REMOVED

        if risks:
            for r in risks:
                if r.reversibility in (
                    ReversibilityClassification.POTENTIALLY_IRREVERSIBLE,
                    ReversibilityClassification.REQUIRES_PRESERVED_DATA,
                ):
                    highest_reversibility = r.reversibility
                if r.priority.rank < highest_priority.rank:
                    highest_priority = r.priority
        elif change.change_type == ComparisonChangeType.REMOVED:
            highest_reversibility = ReversibilityClassification.REQUIRES_PRESERVED_DATA

        # Rollback consideration
        rollback = RollbackConsideration(
            operation_id=op_id,
            reversibility=highest_reversibility,
            is_destructive=is_destructive,
            requires_data_preservation=is_destructive,
            rollback_strategy=self._determine_rollback_strategy(op_type, is_destructive),
            advisory_notes=[
                f"Operation reversibility classified as {highest_reversibility.value}."
            ],
        )

        # Manual decision gates
        manual_gates = self._build_manual_gates(change, op_type, is_destructive, engine_cap)

        is_blocked = engine_cap == EngineCapabilityState.UNSUPPORTED
        blocking_reasons = []
        if is_blocked:
            blocking_reasons.append(
                f"Operation {op_type.value} is unsupported on target engine '{self.target_engine}' without full table rebuild."
            )

        operation = AbstractMigrationOperation(
            operation_id=op_id,
            operation_type=op_type,
            target_object_id=change.canonical_id,
            target_object_type=change.object_type.value,
            target_object_name=change.name,
            namespace=namespace,
            table_name=table_name,
            source_change_fingerprint=change.fingerprint,
            catalog_version=OperationCatalog.CATALOG_VERSION,
            operation_properties=diff_props,
            engine_capability=engine_cap,
            engine_limitations=engine_limits,
            preconditions=preconditions,
            postconditions=postconditions,
            validation_requirements=validation_reqs,
            manual_decision_gates=manual_gates,
            rollback_consideration=rollback,
            source_risk_fingerprint=risks[0].fingerprint if risks else None,
            review_priority=highest_priority,
            is_destructive=is_destructive,
            is_blocked=is_blocked,
            blocking_reasons=blocking_reasons,
        )

        return [operation]

    def _resolve_operation_type(self, change: SchemaChange) -> MigrationOperationType | None:
        """Map ComparisonChangeType and ComparisonObjectType to MigrationOperationType."""
        ct = change.change_type
        ot = change.object_type

        if ot == ComparisonObjectType.NAMESPACE:
            if ct == ComparisonChangeType.ADDED:
                return MigrationOperationType.CREATE_NAMESPACE
            elif ct == ComparisonChangeType.REMOVED:
                return MigrationOperationType.DROP_NAMESPACE
        elif ot == ComparisonObjectType.TABLE:
            if ct == ComparisonChangeType.ADDED:
                return MigrationOperationType.CREATE_TABLE
            elif ct == ComparisonChangeType.REMOVED:
                return MigrationOperationType.DROP_TABLE
        elif ot == ComparisonObjectType.COLUMN:
            if ct == ComparisonChangeType.ADDED:
                return MigrationOperationType.ADD_COLUMN
            elif ct == ComparisonChangeType.REMOVED:
                return MigrationOperationType.DROP_COLUMN
            elif ct == ComparisonChangeType.MODIFIED:
                changed_props = [d.property_name for d in change.property_differences]
                if any(p in ("type", "native_type", "type_category") for p in changed_props):
                    return MigrationOperationType.ALTER_COLUMN_TYPE
                if "is_nullable" in changed_props or "nullable" in changed_props:
                    return MigrationOperationType.ALTER_COLUMN_NULLABILITY
                if "default_expression" in changed_props or "default" in changed_props:
                    return MigrationOperationType.ALTER_COLUMN_DEFAULT
                return MigrationOperationType.ALTER_COLUMN_TYPE
        elif ot == ComparisonObjectType.PRIMARY_KEY:
            if ct == ComparisonChangeType.ADDED:
                return MigrationOperationType.ADD_PRIMARY_KEY
            elif ct == ComparisonChangeType.REMOVED:
                return MigrationOperationType.DROP_PRIMARY_KEY
        elif ot == ComparisonObjectType.UNIQUE_CONSTRAINT:
            if ct == ComparisonChangeType.ADDED:
                return MigrationOperationType.ADD_UNIQUE_CONSTRAINT
            elif ct == ComparisonChangeType.REMOVED:
                return MigrationOperationType.DROP_UNIQUE_CONSTRAINT
        elif ot == ComparisonObjectType.FOREIGN_KEY:
            if ct == ComparisonChangeType.ADDED:
                return MigrationOperationType.ADD_FOREIGN_KEY
            elif ct == ComparisonChangeType.REMOVED:
                return MigrationOperationType.DROP_FOREIGN_KEY
        elif ot == ComparisonObjectType.CHECK_CONSTRAINT:
            if ct == ComparisonChangeType.ADDED:
                return MigrationOperationType.ADD_CHECK_CONSTRAINT
            elif ct == ComparisonChangeType.REMOVED:
                return MigrationOperationType.DROP_CHECK_CONSTRAINT
        elif ot == ComparisonObjectType.INDEX:
            if ct == ComparisonChangeType.ADDED:
                return MigrationOperationType.CREATE_INDEX
            elif ct == ComparisonChangeType.REMOVED:
                return MigrationOperationType.DROP_INDEX
            elif ct == ComparisonChangeType.MODIFIED:
                return MigrationOperationType.MODIFY_INDEX
        elif ot == ComparisonObjectType.VIEW:
            if ct == ComparisonChangeType.ADDED:
                return MigrationOperationType.CREATE_VIEW
            elif ct == ComparisonChangeType.REMOVED:
                return MigrationOperationType.DROP_VIEW
            elif ct == ComparisonChangeType.MODIFIED:
                return MigrationOperationType.MODIFY_VIEW

        return None

    def _build_preconditions(
        self,
        change: SchemaChange,
        op_type: MigrationOperationType,
        entry,
    ) -> list[OperationPrecondition]:
        preconditions = []
        for ptype in entry.default_preconditions:
            preconditions.append(
                OperationPrecondition(
                    condition_id=f"pre_{op_type.value.lower()}_{ptype.value.lower()}_{change.canonical_id}",
                    precondition_type=ptype,
                    description=f"Precondition {ptype.value} for {change.name}.",
                    target_object_id=change.canonical_id,
                    required_evidence="METADATA_INSPECTION",
                    verification_method="CANONICAL_AUDIT",
                    is_satisfied=False,
                    limitations=[],
                )
            )
        return preconditions

    def _build_manual_gates(
        self,
        change: SchemaChange,
        op_type: MigrationOperationType,
        is_destructive: bool,
        engine_cap: EngineCapabilityState,
    ) -> list[ManualDecisionGate]:
        gates = []
        op_id = f"op_{op_type.value.lower()}_{change.canonical_id}"

        if is_destructive:
            gates.append(
                ManualDecisionGate(
                    gate_id=f"gate_data_preservation_{op_id}",
                    operation_id=op_id,
                    title="Data Preservation & Archival Strategy",
                    description=f"Destructive operation {op_type.value} on {change.name} requires verified backup or data archive.",
                    gate_status=ManualGateStatus.REQUIRED,
                    decision_category="DATA_PRESERVATION",
                    required_action="Verify table/column data snapshot is persisted before executing deletion.",
                )
            )

        if op_type in (
            MigrationOperationType.ALTER_COLUMN_TYPE,
            MigrationOperationType.ALTER_COLUMN_NULLABILITY,
            MigrationOperationType.ADD_FOREIGN_KEY,
            MigrationOperationType.ADD_UNIQUE_CONSTRAINT,
            MigrationOperationType.ADD_PRIMARY_KEY,
        ):
            gates.append(
                ManualDecisionGate(
                    gate_id=f"gate_data_validation_{op_id}",
                    operation_id=op_id,
                    title="Existing Data Validation Gate",
                    description=f"Operation {op_type.value} enforces structural constraints that will fail if existing rows violate them.",
                    gate_status=ManualGateStatus.REQUIRED,
                    decision_category="BACKFILL_STRATEGY",
                    required_action="Execute read-only pre-flight query to verify zero nulls/duplicates/orphans exist in target table.",
                )
            )

        if engine_cap == EngineCapabilityState.CONDITIONAL:
            gates.append(
                ManualDecisionGate(
                    gate_id=f"gate_engine_conditional_{op_id}",
                    operation_id=op_id,
                    title=f"Engine Compatibility Verification ({self.target_engine.upper()})",
                    description=f"{op_type.value} is conditional on {self.target_engine}.",
                    gate_status=ManualGateStatus.REQUIRED,
                    decision_category="ENGINE_SPECIFIC_TECHNIQUE",
                    required_action="Review engine limitations and confirm dialect version support before execution.",
                )
            )

        return gates

    def _determine_rollback_strategy(
        self, op_type: MigrationOperationType, is_destructive: bool
    ) -> str:
        if is_destructive:
            return "MANUAL_RESTORE_FROM_BACKUP"
        if op_type == MigrationOperationType.CREATE_TABLE:
            return "DROP TABLE"
        if op_type == MigrationOperationType.ADD_COLUMN:
            return "DROP COLUMN"
        if op_type == MigrationOperationType.ADD_FOREIGN_KEY:
            return "DROP FOREIGN KEY"
        if op_type == MigrationOperationType.CREATE_INDEX:
            return "DROP INDEX"
        if op_type == MigrationOperationType.CREATE_VIEW:
            return "DROP VIEW"
        return "ADVISORY_MANUAL_REVERSAL"
