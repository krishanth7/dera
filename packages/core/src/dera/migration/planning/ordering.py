"""Deterministic Topological Ordering and Stage Grouping.

Calculates a deterministic topological sequence of migration operations using Kahn's algorithm
with lexicographical tie-breaking over operation IDs and priority.
Groups operations into sequential PlanningStages without violating any dependency order.
"""

from typing import Dict, List, Set, Tuple
from dera.migration.planning.enums import MigrationOperationType, PlanningStageType
from dera.migration.planning.graph import OperationDependencyGraph
from dera.migration.planning.models import AbstractMigrationOperation, PlanningStage


class DeterministicOrderingEngine:
    """Computes deterministic topological ordering and stages for migration operations."""

    def __init__(self, graph: OperationDependencyGraph):
        self.graph = graph

    def compute_ordering(self) -> Tuple[List[AbstractMigrationOperation], List[PlanningStage]]:
        """Compute deterministic topological sort and planning stages."""
        in_degree: Dict[str, int] = {
            op_id: len(prereqs) for op_id, prereqs in self.graph.reverse_edges.items()
        }

        # Available queue: nodes with in_degree == 0
        # Sorted lexicographically by operation_id for stable tie-breaking
        ready: List[str] = sorted([op_id for op_id, deg in in_degree.items() if deg == 0])

        ordered_op_ids: List[str] = []

        while ready:
            # Deterministic pick: lexicographical order of operation_id
            curr_id = ready.pop(0)
            ordered_op_ids.append(curr_id)

            for dependent_id in sorted(self.graph.forward_edges.get(curr_id, set())):
                in_degree[dependent_id] -= 1
                if in_degree[dependent_id] == 0:
                    ready.append(dependent_id)
                    ready.sort()  # Maintain deterministic tie-breaking

        ordered_ops = [self.graph.operations[op_id] for op_id in ordered_op_ids]

        # Group into stages
        stages = self._group_into_stages(ordered_ops)

        return ordered_ops, stages

    def _group_into_stages(self, ordered_ops: List[AbstractMigrationOperation]) -> List[PlanningStage]:
        """Group operations into 7 sequential logical planning stages."""
        stage_buckets: Dict[PlanningStageType, List[str]] = {
            PlanningStageType.PREREQUISITE_VERIFICATION: [],
            PlanningStageType.STRUCTURAL_PREPARATION: [],
            PlanningStageType.DEPENDENCY_ADJUSTMENT: [],
            PlanningStageType.SCHEMA_MODIFICATION: [],
            PlanningStageType.CONSTRAINT_ESTABLISHMENT: [],
            PlanningStageType.VALIDATION: [],
            PlanningStageType.FINAL_REVIEW: [],
        }

        for op in ordered_ops:
            stype = self._map_operation_to_stage_type(op.operation_type)
            stage_buckets[stype].append(op.operation_id)

        stages: List[PlanningStage] = []
        stage_order = 1
        stage_descriptions = {
            PlanningStageType.PREREQUISITE_VERIFICATION: "Verify namespaces, prerequisites, and operational environments.",
            PlanningStageType.STRUCTURAL_PREPARATION: "Create namespaces and prerequisite base structures.",
            PlanningStageType.DEPENDENCY_ADJUSTMENT: "Drop dependent foreign keys, constraints, or views before structural alteration.",
            PlanningStageType.SCHEMA_MODIFICATION: "Create tables, alter columns, add/drop columns, and drop tables.",
            PlanningStageType.CONSTRAINT_ESTABLISHMENT: "Establish foreign keys, unique constraints, and secondary indexes.",
            PlanningStageType.VALIDATION: "Re-create views, execute post-migration validation checks, and verify integrity.",
            PlanningStageType.FINAL_REVIEW: "Review final state metadata and verify closure.",
        }

        for stype in PlanningStageType:
            op_ids = stage_buckets[stype]
            if op_ids:
                stages.append(
                    PlanningStage(
                        stage_id=f"stage_{stage_order}_{stype.value.lower()}",
                        stage_type=stype,
                        stage_order=stage_order,
                        operation_ids=op_ids,
                        description=stage_descriptions[stype],
                    )
                )
                stage_order += 1

        return stages

    def _map_operation_to_stage_type(self, op_type: MigrationOperationType) -> PlanningStageType:
        """Map abstract operation to logical lifecycle planning stage."""
        if op_type in (MigrationOperationType.CREATE_NAMESPACE,):
            return PlanningStageType.STRUCTURAL_PREPARATION

        if op_type in (
            MigrationOperationType.DROP_FOREIGN_KEY,
            MigrationOperationType.DROP_INDEX,
            MigrationOperationType.DROP_VIEW,
            MigrationOperationType.DROP_UNIQUE_CONSTRAINT,
            MigrationOperationType.DROP_CHECK_CONSTRAINT,
            MigrationOperationType.DROP_PRIMARY_KEY,
        ):
            return PlanningStageType.DEPENDENCY_ADJUSTMENT

        if op_type in (
            MigrationOperationType.CREATE_TABLE,
            MigrationOperationType.ADD_COLUMN,
            MigrationOperationType.DROP_COLUMN,
            MigrationOperationType.ALTER_COLUMN_TYPE,
            MigrationOperationType.ALTER_COLUMN_NULLABILITY,
            MigrationOperationType.ALTER_COLUMN_DEFAULT,
            MigrationOperationType.DROP_TABLE,
            MigrationOperationType.DROP_NAMESPACE,
        ):
            return PlanningStageType.SCHEMA_MODIFICATION

        if op_type in (
            MigrationOperationType.ADD_PRIMARY_KEY,
            MigrationOperationType.ADD_UNIQUE_CONSTRAINT,
            MigrationOperationType.ADD_FOREIGN_KEY,
            MigrationOperationType.ADD_CHECK_CONSTRAINT,
            MigrationOperationType.CREATE_INDEX,
            MigrationOperationType.MODIFY_INDEX,
        ):
            return PlanningStageType.CONSTRAINT_ESTABLISHMENT

        if op_type in (
            MigrationOperationType.CREATE_VIEW,
            MigrationOperationType.MODIFY_VIEW,
        ):
            return PlanningStageType.VALIDATION

        return PlanningStageType.SCHEMA_MODIFICATION
