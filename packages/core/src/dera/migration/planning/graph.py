"""Migration Operation Dependency Graph.

Builds a directed acyclic graph (DAG) of migration operations enforcing:
    Prerequisite Operation -> Dependent Operation

Explicit Rules:
1. Namespace Creation -> Table Creation (within namespace).
2. Table Creation -> Column Addition / Table Indexes / Constraints / Primary Keys.
3. Referenced Table Creation -> Referencing Table Foreign Key Creation.
4. Foreign Key Removal -> Referenced Table Drop (to prevent foreign key violations on drop).
5. Column Removal -> Table Drop (or drop column before drop table if partial, but drop table drops all columns).
6. Index/Constraint Removal -> Column Drop (dependent on that index/constraint).
7. View Dependencies: Referenced Tables -> View Creation.
"""

from dera.migration.planning.enums import MigrationOperationType
from dera.migration.planning.models import AbstractMigrationOperation


class OperationDependencyGraph:
    """Directed graph representing migration operation prerequisites."""

    def __init__(self, operations: list[AbstractMigrationOperation]):
        self.operations: dict[str, AbstractMigrationOperation] = {
            op.operation_id: op for op in operations
        }
        # Adjacency lists:
        # forward_edges: prerequisite_id -> list of dependent_ids
        # reverse_edges: dependent_id -> list of prerequisite_ids
        self.forward_edges: dict[str, set[str]] = {op.operation_id: set() for op in operations}
        self.reverse_edges: dict[str, set[str]] = {op.operation_id: set() for op in operations}
        self._build_graph()

    def add_dependency(self, prerequisite_id: str, dependent_id: str) -> None:
        """Add directed edge: prerequisite_id -> dependent_id."""
        if prerequisite_id == dependent_id:
            # Self dependency is a direct cycle
            return
        if prerequisite_id in self.operations and dependent_id in self.operations:
            self.forward_edges[prerequisite_id].add(dependent_id)
            self.reverse_edges[dependent_id].add(prerequisite_id)

    def _build_graph(self) -> None:
        """Extract and link operation dependencies based on structural rules."""
        # Index operations by table and namespace
        table_create_ops: dict[tuple[str, str], str] = {}  # (ns, table) -> op_id
        table_drop_ops: dict[tuple[str, str], str] = {}  # (ns, table) -> op_id
        fk_create_ops: list[AbstractMigrationOperation] = []
        fk_drop_ops: list[AbstractMigrationOperation] = []

        for op in self.operations.values():
            ns = op.namespace or "public"
            tbl = op.table_name or op.target_object_name
            if op.operation_type == MigrationOperationType.CREATE_TABLE:
                table_create_ops[(ns, tbl)] = op.operation_id
            elif op.operation_type == MigrationOperationType.DROP_TABLE:
                table_drop_ops[(ns, tbl)] = op.operation_id
            elif op.operation_type == MigrationOperationType.ADD_FOREIGN_KEY:
                fk_create_ops.append(op)
            elif op.operation_type == MigrationOperationType.DROP_FOREIGN_KEY:
                fk_drop_ops.append(op)

        # Rule 1: Table Creation -> Column/Index/PK/Constraint Additions on same table
        for op in self.operations.values():
            ns = op.namespace or "public"
            tbl = op.table_name or op.target_object_name

            if (ns, tbl) in table_create_ops and op.operation_id != table_create_ops[(ns, tbl)]:
                # If creating table, column/index/pk additions must follow table creation
                if op.operation_type in (
                    MigrationOperationType.ADD_COLUMN,
                    MigrationOperationType.ADD_PRIMARY_KEY,
                    MigrationOperationType.ADD_UNIQUE_CONSTRAINT,
                    MigrationOperationType.ADD_FOREIGN_KEY,
                    MigrationOperationType.ADD_CHECK_CONSTRAINT,
                    MigrationOperationType.CREATE_INDEX,
                ):
                    self.add_dependency(table_create_ops[(ns, tbl)], op.operation_id)

            # Rule 2: Column/Index/FK/PK Drops -> Table Drop
            if (ns, tbl) in table_drop_ops and op.operation_id != table_drop_ops[(ns, tbl)]:
                if op.operation_type in (
                    MigrationOperationType.DROP_FOREIGN_KEY,
                    MigrationOperationType.DROP_INDEX,
                    MigrationOperationType.DROP_UNIQUE_CONSTRAINT,
                    MigrationOperationType.DROP_CHECK_CONSTRAINT,
                    MigrationOperationType.DROP_PRIMARY_KEY,
                    MigrationOperationType.DROP_COLUMN,
                ):
                    self.add_dependency(op.operation_id, table_drop_ops[(ns, tbl)])

        # Rule 3: Referenced Table Creation -> Referencing Table Foreign Key Creation
        for fk_op in fk_create_ops:
            props = fk_op.operation_properties
            ref_tbl = props.get("referenced_table")
            ref_ns = props.get("referenced_schema", fk_op.namespace or "public")
            if ref_tbl and (ref_ns, ref_tbl) in table_create_ops:
                # Parent table must be created before adding FK to child table
                self.add_dependency(table_create_ops[(ref_ns, ref_tbl)], fk_op.operation_id)

        # Rule 4: Drop Foreign Key before Drop Referenced Table
        for fk_op in fk_drop_ops:
            props = fk_op.operation_properties
            ref_tbl = props.get("referenced_table")
            ref_ns = props.get("referenced_schema", fk_op.namespace or "public")
            if ref_tbl and (ref_ns, ref_tbl) in table_drop_ops:
                # Dropping foreign key must precede dropping referenced parent table
                self.add_dependency(fk_op.operation_id, table_drop_ops[(ref_ns, ref_tbl)])

        # Populate operation model bidirectional references
        for op_id, op in self.operations.items():
            op.prerequisite_operation_ids = sorted(list(self.reverse_edges[op_id]))
            op.dependent_operation_ids = sorted(list(self.forward_edges[op_id]))

    @property
    def edge_count(self) -> int:
        return sum(len(deps) for deps in self.forward_edges.values())
