"""Deterministic test fixtures for Phase 6.3 Foreign Key Relationship Graph.

Provides test databases and schema fixtures for:
- Simple 1-to-N relationships
- Composite foreign keys
- Self-referencing (self-loop) foreign keys
- Parallel edges (multiple foreign keys between same tables)
- Cross-namespace foreign keys
- Unresolved foreign key targets (missing referenced table)
- Restricted metadata
- Multi-engine schemas (PostgreSQL, SQLite, MySQL, MariaDB)
- Disconnected multi-component graphs
"""

from __future__ import annotations

from datetime import UTC, datetime

from dera.metadata.enums import (
    CanonicalTypeCategory,
    ConstraintType,
    ForeignKeyAction,
    MetadataCompleteness,
    ObjectKind,
    TableType,
)
from dera.metadata.identity import compute_stable_object_id
from dera.metadata.models import (
    CanonicalColumn,
    CanonicalConstraint,
    CanonicalDatabase,
    CanonicalForeignKey,
    CanonicalNamespace,
    CanonicalTable,
)
from dera.metadata.provenance import MetadataProvenance


def make_graph_provenance(
    engine: str = "postgresql",
    identifier: str = "test",
    completeness: MetadataCompleteness = MetadataCompleteness.COMPLETE,
) -> MetadataProvenance:
    """Create a deterministic MetadataProvenance record for tests."""
    return MetadataProvenance(
        source_engine=engine,
        source_version="16.0" if "postgres" in engine else "3.42.0",
        connector_version="1.0.0",
        collection_timestamp=datetime(2026, 10, 28, 12, 0, 0, tzinfo=UTC),
        completeness=completeness,
        native_identifier=identifier,
    )


def make_test_column(
    table_id: str,
    name: str,
    ordinal: int,
    engine: str = "postgresql",
    workspace_id: str | None = "test-ws",
) -> CanonicalColumn:
    """Helper to create a CanonicalColumn."""
    col_id = compute_stable_object_id(
        engine=engine,
        object_kind=ObjectKind.COLUMN,
        native_name=name,
        parent_id=table_id,
        workspace_id=workspace_id,
    )
    return CanonicalColumn(
        id=col_id,
        table_id=table_id,
        name=name,
        ordinal_position=ordinal,
        native_type="integer",
        canonical_type=CanonicalTypeCategory.INTEGER,
        is_nullable=False,
        provenance=make_graph_provenance(engine=engine, identifier=name),
    )


def make_simple_fk_schema(
    engine: str = "postgresql",
    workspace_id: str | None = "test-ws",
) -> CanonicalDatabase:
    """Creates customers (id) and orders (id, customer_id -> customers.id)."""
    db_id = compute_stable_object_id(
        engine=engine,
        object_kind=ObjectKind.DATABASE,
        native_name="test_db",
        workspace_id=workspace_id,
    )
    ns_id = compute_stable_object_id(
        engine=engine,
        object_kind=ObjectKind.NAMESPACE,
        native_name="public",
        parent_id=db_id,
        workspace_id=workspace_id,
    )

    # Customers Table
    cust_id = compute_stable_object_id(
        engine=engine,
        object_kind=ObjectKind.TABLE,
        native_name="customers",
        parent_id=ns_id,
        workspace_id=workspace_id,
    )
    cust_pk_id = compute_stable_object_id(
        engine=engine,
        object_kind=ObjectKind.PRIMARY_KEY,
        native_name="pk_customers",
        parent_id=cust_id,
        workspace_id=workspace_id,
    )
    cust_pk = CanonicalConstraint(
        id=cust_pk_id,
        table_id=cust_id,
        name="pk_customers",
        constraint_type=ConstraintType.PRIMARY_KEY,
        column_names=("id",),
        column_ids=(
            compute_stable_object_id(
                engine=engine,
                object_kind=ObjectKind.COLUMN,
                native_name="id",
                parent_id=cust_id,
                workspace_id=workspace_id,
            ),
        ),
        provenance=make_graph_provenance(engine=engine, identifier="pk_customers"),
    )
    cust_table = CanonicalTable(
        id=cust_id,
        namespace_id=ns_id,
        name="customers",
        schema_name="public",
        table_type=TableType.TABLE,
        columns=(
            make_test_column(cust_id, "id", 1, engine=engine, workspace_id=workspace_id),
            make_test_column(cust_id, "name", 2, engine=engine, workspace_id=workspace_id),
        ),
        primary_key=cust_pk,
        provenance=make_graph_provenance(engine=engine, identifier="customers"),
    )

    # Orders Table
    ord_id = compute_stable_object_id(
        engine=engine,
        object_kind=ObjectKind.TABLE,
        native_name="orders",
        parent_id=ns_id,
        workspace_id=workspace_id,
    )
    fk_id = compute_stable_object_id(
        engine=engine,
        object_kind=ObjectKind.FOREIGN_KEY,
        native_name="fk_orders_customer",
        parent_id=ord_id,
        workspace_id=workspace_id,
    )
    fk = CanonicalForeignKey(
        id=fk_id,
        table_id=ord_id,
        name="fk_orders_customer",
        column_names=("customer_id",),
        column_ids=(
            compute_stable_object_id(
                engine=engine,
                object_kind=ObjectKind.COLUMN,
                native_name="customer_id",
                parent_id=ord_id,
                workspace_id=workspace_id,
            ),
        ),
        referenced_table_id=cust_id,
        referenced_schema_name="public",
        referenced_table_name="customers",
        referenced_column_names=("id",),
        referenced_column_ids=(cust_table.columns[0].id,),
        on_delete=ForeignKeyAction.CASCADE,
        on_update=ForeignKeyAction.NO_ACTION,
        provenance=make_graph_provenance(engine=engine, identifier="fk_orders_customer"),
    )
    ord_table = CanonicalTable(
        id=ord_id,
        namespace_id=ns_id,
        name="orders",
        schema_name="public",
        table_type=TableType.TABLE,
        columns=(
            make_test_column(ord_id, "id", 1, engine=engine, workspace_id=workspace_id),
            make_test_column(ord_id, "customer_id", 2, engine=engine, workspace_id=workspace_id),
        ),
        foreign_keys=(fk,),
        provenance=make_graph_provenance(engine=engine, identifier="orders"),
    )

    return CanonicalDatabase(
        id=db_id,
        name="test_db",
        engine=engine,
        namespaces=(
            CanonicalNamespace(
                id=ns_id,
                name="public",
                tables=(cust_table, ord_table),
                provenance=make_graph_provenance(engine=engine, identifier="public"),
            ),
        ),
        provenance=make_graph_provenance(engine=engine, identifier="test_db"),
    )


def make_composite_fk_schema(
    engine: str = "postgresql",
    workspace_id: str | None = "test-ws",
) -> CanonicalDatabase:
    """Creates parent branches (tenant_id, branch_id) and child employees (emp_id, tenant_id, branch_id)."""
    db_id = compute_stable_object_id(
        engine=engine,
        object_kind=ObjectKind.DATABASE,
        native_name="comp_db",
        workspace_id=workspace_id,
    )
    ns_id = compute_stable_object_id(
        engine=engine,
        object_kind=ObjectKind.NAMESPACE,
        native_name="public",
        parent_id=db_id,
        workspace_id=workspace_id,
    )

    # Branches table
    br_id = compute_stable_object_id(
        engine=engine,
        object_kind=ObjectKind.TABLE,
        native_name="branches",
        parent_id=ns_id,
        workspace_id=workspace_id,
    )
    br_table = CanonicalTable(
        id=br_id,
        namespace_id=ns_id,
        name="branches",
        schema_name="public",
        columns=(
            make_test_column(br_id, "tenant_id", 1, engine=engine, workspace_id=workspace_id),
            make_test_column(br_id, "branch_id", 2, engine=engine, workspace_id=workspace_id),
        ),
        primary_key=CanonicalConstraint(
            id=compute_stable_object_id(
                engine=engine,
                object_kind=ObjectKind.PRIMARY_KEY,
                native_name="pk_branches",
                parent_id=br_id,
                workspace_id=workspace_id,
            ),
            table_id=br_id,
            name="pk_branches",
            constraint_type=ConstraintType.PRIMARY_KEY,
            column_names=("tenant_id", "branch_id"),
            column_ids=(
                compute_stable_object_id(
                    engine=engine,
                    object_kind=ObjectKind.COLUMN,
                    native_name="tenant_id",
                    parent_id=br_id,
                    workspace_id=workspace_id,
                ),
                compute_stable_object_id(
                    engine=engine,
                    object_kind=ObjectKind.COLUMN,
                    native_name="branch_id",
                    parent_id=br_id,
                    workspace_id=workspace_id,
                ),
            ),
            provenance=make_graph_provenance(engine=engine),
        ),
        provenance=make_graph_provenance(engine=engine),
    )

    # Employees table with composite foreign key
    emp_id = compute_stable_object_id(
        engine=engine,
        object_kind=ObjectKind.TABLE,
        native_name="employees",
        parent_id=ns_id,
        workspace_id=workspace_id,
    )
    comp_fk = CanonicalForeignKey(
        id=compute_stable_object_id(
            engine=engine,
            object_kind=ObjectKind.FOREIGN_KEY,
            native_name="fk_emp_branches",
            parent_id=emp_id,
            workspace_id=workspace_id,
        ),
        table_id=emp_id,
        name="fk_emp_branches",
        column_names=("tenant_id", "branch_id"),
        column_ids=(
            compute_stable_object_id(
                engine=engine,
                object_kind=ObjectKind.COLUMN,
                native_name="tenant_id",
                parent_id=emp_id,
                workspace_id=workspace_id,
            ),
            compute_stable_object_id(
                engine=engine,
                object_kind=ObjectKind.COLUMN,
                native_name="branch_id",
                parent_id=emp_id,
                workspace_id=workspace_id,
            ),
        ),
        referenced_table_id=br_id,
        referenced_schema_name="public",
        referenced_table_name="branches",
        referenced_column_names=("tenant_id", "branch_id"),
        referenced_column_ids=(br_table.columns[0].id, br_table.columns[1].id),
        on_delete=ForeignKeyAction.RESTRICT,
        on_update=ForeignKeyAction.CASCADE,
        is_composite=True,
        provenance=make_graph_provenance(engine=engine),
    )
    emp_table = CanonicalTable(
        id=emp_id,
        namespace_id=ns_id,
        name="employees",
        schema_name="public",
        columns=(
            make_test_column(emp_id, "emp_id", 1, engine=engine, workspace_id=workspace_id),
            make_test_column(emp_id, "tenant_id", 2, engine=engine, workspace_id=workspace_id),
            make_test_column(emp_id, "branch_id", 3, engine=engine, workspace_id=workspace_id),
        ),
        foreign_keys=(comp_fk,),
        provenance=make_graph_provenance(engine=engine),
    )

    return CanonicalDatabase(
        id=db_id,
        name="comp_db",
        engine=engine,
        namespaces=(
            CanonicalNamespace(
                id=ns_id,
                name="public",
                tables=(br_table, emp_table),
                provenance=make_graph_provenance(engine=engine),
            ),
        ),
        provenance=make_graph_provenance(engine=engine),
    )


def make_self_referencing_schema(
    engine: str = "postgresql",
    workspace_id: str | None = "test-ws",
) -> CanonicalDatabase:
    """Creates categories table with parent_category_id -> categories.id."""
    db_id = compute_stable_object_id(
        engine=engine,
        object_kind=ObjectKind.DATABASE,
        native_name="self_db",
        workspace_id=workspace_id,
    )
    ns_id = compute_stable_object_id(
        engine=engine,
        object_kind=ObjectKind.NAMESPACE,
        native_name="public",
        parent_id=db_id,
        workspace_id=workspace_id,
    )

    cat_id = compute_stable_object_id(
        engine=engine,
        object_kind=ObjectKind.TABLE,
        native_name="categories",
        parent_id=ns_id,
        workspace_id=workspace_id,
    )
    cat_fk = CanonicalForeignKey(
        id=compute_stable_object_id(
            engine=engine,
            object_kind=ObjectKind.FOREIGN_KEY,
            native_name="fk_cat_parent",
            parent_id=cat_id,
            workspace_id=workspace_id,
        ),
        table_id=cat_id,
        name="fk_cat_parent",
        column_names=("parent_id",),
        column_ids=(
            compute_stable_object_id(
                engine=engine,
                object_kind=ObjectKind.COLUMN,
                native_name="parent_id",
                parent_id=cat_id,
                workspace_id=workspace_id,
            ),
        ),
        referenced_table_id=cat_id,
        referenced_schema_name="public",
        referenced_table_name="categories",
        referenced_column_names=("id",),
        referenced_column_ids=(
            compute_stable_object_id(
                engine=engine,
                object_kind=ObjectKind.COLUMN,
                native_name="id",
                parent_id=cat_id,
                workspace_id=workspace_id,
            ),
        ),
        on_delete=ForeignKeyAction.SET_NULL,
        provenance=make_graph_provenance(engine=engine),
    )
    cat_table = CanonicalTable(
        id=cat_id,
        namespace_id=ns_id,
        name="categories",
        schema_name="public",
        columns=(
            make_test_column(cat_id, "id", 1, engine=engine, workspace_id=workspace_id),
            make_test_column(cat_id, "parent_id", 2, engine=engine, workspace_id=workspace_id),
        ),
        foreign_keys=(cat_fk,),
        provenance=make_graph_provenance(engine=engine),
    )

    return CanonicalDatabase(
        id=db_id,
        name="self_db",
        engine=engine,
        namespaces=(
            CanonicalNamespace(
                id=ns_id,
                name="public",
                tables=(cat_table,),
                provenance=make_graph_provenance(engine=engine),
            ),
        ),
        provenance=make_graph_provenance(engine=engine),
    )


def make_parallel_edges_schema(
    engine: str = "postgresql",
    workspace_id: str | None = "test-ws",
) -> CanonicalDatabase:
    """Creates users and tasks where tasks has created_by_id and assigned_to_id both referencing users.id."""
    db_id = compute_stable_object_id(
        engine=engine,
        object_kind=ObjectKind.DATABASE,
        native_name="parallel_db",
        workspace_id=workspace_id,
    )
    ns_id = compute_stable_object_id(
        engine=engine,
        object_kind=ObjectKind.NAMESPACE,
        native_name="public",
        parent_id=db_id,
        workspace_id=workspace_id,
    )

    u_id = compute_stable_object_id(
        engine=engine,
        object_kind=ObjectKind.TABLE,
        native_name="users",
        parent_id=ns_id,
        workspace_id=workspace_id,
    )
    u_table = CanonicalTable(
        id=u_id,
        namespace_id=ns_id,
        name="users",
        schema_name="public",
        columns=(make_test_column(u_id, "id", 1, engine=engine, workspace_id=workspace_id),),
        provenance=make_graph_provenance(engine=engine),
    )

    t_id = compute_stable_object_id(
        engine=engine,
        object_kind=ObjectKind.TABLE,
        native_name="tasks",
        parent_id=ns_id,
        workspace_id=workspace_id,
    )
    fk1 = CanonicalForeignKey(
        id=compute_stable_object_id(
            engine=engine,
            object_kind=ObjectKind.FOREIGN_KEY,
            native_name="fk_tasks_creator",
            parent_id=t_id,
            workspace_id=workspace_id,
        ),
        table_id=t_id,
        name="fk_tasks_creator",
        column_names=("created_by",),
        referenced_table_id=u_id,
        referenced_schema_name="public",
        referenced_table_name="users",
        referenced_column_names=("id",),
        provenance=make_graph_provenance(engine=engine),
    )
    fk2 = CanonicalForeignKey(
        id=compute_stable_object_id(
            engine=engine,
            object_kind=ObjectKind.FOREIGN_KEY,
            native_name="fk_tasks_assignee",
            parent_id=t_id,
            workspace_id=workspace_id,
        ),
        table_id=t_id,
        name="fk_tasks_assignee",
        column_names=("assigned_to",),
        referenced_table_id=u_id,
        referenced_schema_name="public",
        referenced_table_name="users",
        referenced_column_names=("id",),
        provenance=make_graph_provenance(engine=engine),
    )
    t_table = CanonicalTable(
        id=t_id,
        namespace_id=ns_id,
        name="tasks",
        schema_name="public",
        columns=(
            make_test_column(t_id, "id", 1, engine=engine, workspace_id=workspace_id),
            make_test_column(t_id, "created_by", 2, engine=engine, workspace_id=workspace_id),
            make_test_column(t_id, "assigned_to", 3, engine=engine, workspace_id=workspace_id),
        ),
        foreign_keys=(fk1, fk2),
        provenance=make_graph_provenance(engine=engine),
    )

    return CanonicalDatabase(
        id=db_id,
        name="parallel_db",
        engine=engine,
        namespaces=(
            CanonicalNamespace(
                id=ns_id,
                name="public",
                tables=(u_table, t_table),
                provenance=make_graph_provenance(engine=engine),
            ),
        ),
        provenance=make_graph_provenance(engine=engine),
    )


def make_cross_namespace_schema(
    engine: str = "postgresql",
    workspace_id: str | None = "test-ws",
) -> CanonicalDatabase:
    """Creates auth.users and app.profiles with cross-namespace foreign key."""
    db_id = compute_stable_object_id(
        engine=engine,
        object_kind=ObjectKind.DATABASE,
        native_name="cross_db",
        workspace_id=workspace_id,
    )
    ns_auth = compute_stable_object_id(
        engine=engine,
        object_kind=ObjectKind.NAMESPACE,
        native_name="auth",
        parent_id=db_id,
        workspace_id=workspace_id,
    )
    ns_app = compute_stable_object_id(
        engine=engine,
        object_kind=ObjectKind.NAMESPACE,
        native_name="app",
        parent_id=db_id,
        workspace_id=workspace_id,
    )

    u_id = compute_stable_object_id(
        engine=engine,
        object_kind=ObjectKind.TABLE,
        native_name="users",
        parent_id=ns_auth,
        workspace_id=workspace_id,
    )
    u_table = CanonicalTable(
        id=u_id,
        namespace_id=ns_auth,
        name="users",
        schema_name="auth",
        columns=(make_test_column(u_id, "id", 1, engine=engine, workspace_id=workspace_id),),
        provenance=make_graph_provenance(engine=engine),
    )

    p_id = compute_stable_object_id(
        engine=engine,
        object_kind=ObjectKind.TABLE,
        native_name="profiles",
        parent_id=ns_app,
        workspace_id=workspace_id,
    )
    fk = CanonicalForeignKey(
        id=compute_stable_object_id(
            engine=engine,
            object_kind=ObjectKind.FOREIGN_KEY,
            native_name="fk_profiles_user",
            parent_id=p_id,
            workspace_id=workspace_id,
        ),
        table_id=p_id,
        name="fk_profiles_user",
        column_names=("user_id",),
        referenced_table_id=u_id,
        referenced_schema_name="auth",
        referenced_table_name="users",
        referenced_column_names=("id",),
        provenance=make_graph_provenance(engine=engine),
    )
    p_table = CanonicalTable(
        id=p_id,
        namespace_id=ns_app,
        name="profiles",
        schema_name="app",
        columns=(
            make_test_column(p_id, "id", 1, engine=engine, workspace_id=workspace_id),
            make_test_column(p_id, "user_id", 2, engine=engine, workspace_id=workspace_id),
        ),
        foreign_keys=(fk,),
        provenance=make_graph_provenance(engine=engine),
    )

    return CanonicalDatabase(
        id=db_id,
        name="cross_db",
        engine=engine,
        namespaces=(
            CanonicalNamespace(
                id=ns_auth,
                name="auth",
                tables=(u_table,),
                provenance=make_graph_provenance(engine=engine),
            ),
            CanonicalNamespace(
                id=ns_app,
                name="app",
                tables=(p_table,),
                provenance=make_graph_provenance(engine=engine),
            ),
        ),
        provenance=make_graph_provenance(engine=engine),
    )


def make_unresolved_fk_schema(
    engine: str = "postgresql",
    workspace_id: str | None = "test-ws",
) -> CanonicalDatabase:
    """Creates a table referencing an uninspected/non-existent external table."""
    db_id = compute_stable_object_id(
        engine=engine,
        object_kind=ObjectKind.DATABASE,
        native_name="unres_db",
        workspace_id=workspace_id,
    )
    ns_id = compute_stable_object_id(
        engine=engine,
        object_kind=ObjectKind.NAMESPACE,
        native_name="public",
        parent_id=db_id,
        workspace_id=workspace_id,
    )

    o_id = compute_stable_object_id(
        engine=engine,
        object_kind=ObjectKind.TABLE,
        native_name="orders",
        parent_id=ns_id,
        workspace_id=workspace_id,
    )
    fk = CanonicalForeignKey(
        id=compute_stable_object_id(
            engine=engine,
            object_kind=ObjectKind.FOREIGN_KEY,
            native_name="fk_orders_ext",
            parent_id=o_id,
            workspace_id=workspace_id,
        ),
        table_id=o_id,
        name="fk_orders_ext",
        column_names=("customer_id",),
        referenced_table_id=None,
        referenced_schema_name="legacy",
        referenced_table_name="external_customers",
        referenced_column_names=("id",),
        provenance=make_graph_provenance(engine=engine),
    )
    o_table = CanonicalTable(
        id=o_id,
        namespace_id=ns_id,
        name="orders",
        schema_name="public",
        columns=(
            make_test_column(o_id, "id", 1, engine=engine, workspace_id=workspace_id),
            make_test_column(o_id, "customer_id", 2, engine=engine, workspace_id=workspace_id),
        ),
        foreign_keys=(fk,),
        provenance=make_graph_provenance(engine=engine),
    )

    return CanonicalDatabase(
        id=db_id,
        name="unres_db",
        engine=engine,
        namespaces=(
            CanonicalNamespace(
                id=ns_id,
                name="public",
                tables=(o_table,),
                provenance=make_graph_provenance(engine=engine),
            ),
        ),
        provenance=make_graph_provenance(engine=engine),
    )
