"""Deterministic test fixtures for Phase 6.4 Dependency Analysis & Cycle Detection.

Provides deterministic CanonicalDatabase fixtures for:
- Linear DAG dependency chains
- Diamond DAG structures
- Self-referencing tables (single-node cycles)
- Mutual 2-table cycles (with nullable and NOT NULL variations)
- Indirect multi-table cycles (3+ tables)
- Complex intertwined multi-cycle SCCs
- Disjoint multi-component DAGs
- Multi-engine e-commerce production schema
"""

from __future__ import annotations

from datetime import UTC, datetime

from dera.metadata.enums import (
    CanonicalTypeCategory,
    ForeignKeyAction,
    MetadataCompleteness,
    ObjectKind,
    TableType,
)
from dera.metadata.identity import compute_stable_object_id
from dera.metadata.models import (
    CanonicalColumn,
    CanonicalDatabase,
    CanonicalForeignKey,
    CanonicalNamespace,
    CanonicalTable,
)
from dera.metadata.provenance import MetadataProvenance
from dera.reverse_engineering.dependencies.analyzer import DependencyAnalyzer
from dera.reverse_engineering.dependencies.models import DependencyAnalysisResult
from dera.reverse_engineering.graph.builder import ForeignKeyGraphBuilder


def make_dep_provenance(
    engine: str = "postgresql",
    identifier: str = "test",
    completeness: MetadataCompleteness = MetadataCompleteness.COMPLETE,
) -> MetadataProvenance:
    """Create a deterministic MetadataProvenance record for dependency tests."""
    return MetadataProvenance(
        source_engine=engine,
        source_version="16.0" if "postgres" in engine else "3.42.0",
        connector_version="1.0.0",
        collection_timestamp=datetime(2026, 10, 28, 12, 0, 0, tzinfo=UTC),
        completeness=completeness,
        native_identifier=identifier,
    )


def make_col(
    table_id: str,
    name: str,
    ordinal: int,
    is_nullable: bool = False,
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
        is_nullable=is_nullable,
        provenance=make_dep_provenance(engine=engine, identifier=name),
    )


def make_linear_dag_schema(
    engine: str = "postgresql",
    workspace_id: str | None = "test-ws",
) -> CanonicalDatabase:
    """Creates a 4-table linear dependency chain: t0 <- t1 <- t2 <- t3."""
    db_id = compute_stable_object_id(
        engine=engine,
        object_kind=ObjectKind.DATABASE,
        native_name="linear_db",
        workspace_id=workspace_id,
    )
    ns_id = compute_stable_object_id(
        engine=engine,
        object_kind=ObjectKind.NAMESPACE,
        native_name="public",
        parent_id=db_id,
        workspace_id=workspace_id,
    )

    tables: list[CanonicalTable] = []
    prev_id = None
    prev_name = None

    for i in range(4):
        name = f"t{i}"
        tid = compute_stable_object_id(
            engine=engine,
            object_kind=ObjectKind.TABLE,
            native_name=name,
            parent_id=ns_id,
            workspace_id=workspace_id,
        )
        id_col = make_col(tid, "id", 1, engine=engine, workspace_id=workspace_id)
        cols = [id_col]
        fks = []

        if prev_id and prev_name:
            ref_col = make_col(tid, f"{prev_name}_id", 2, engine=engine, workspace_id=workspace_id)
            cols.append(ref_col)
            fk_id = compute_stable_object_id(
                engine=engine,
                object_kind=ObjectKind.FOREIGN_KEY,
                native_name=f"fk_{name}_{prev_name}",
                parent_id=tid,
                workspace_id=workspace_id,
            )
            fk = CanonicalForeignKey(
                id=fk_id,
                table_id=tid,
                name=f"fk_{name}_{prev_name}",
                column_names=(f"{prev_name}_id",),
                referenced_table_id=prev_id,
                referenced_schema_name="public",
                referenced_table_name=prev_name,
                referenced_column_names=("id",),
                on_delete=ForeignKeyAction.NO_ACTION,
                on_update=ForeignKeyAction.NO_ACTION,
                provenance=make_dep_provenance(engine=engine, identifier=f"fk_{name}_{prev_name}"),
            )
            fks.append(fk)

        tables.append(
            CanonicalTable(
                id=tid,
                namespace_id=ns_id,
                name=name,
                schema_name="public",
                table_type=TableType.TABLE,
                columns=tuple(cols),
                foreign_keys=tuple(fks),
                provenance=make_dep_provenance(engine=engine, identifier=name),
            )
        )
        prev_id = tid
        prev_name = name

    return CanonicalDatabase(
        id=db_id,
        name="linear_db",
        engine=engine,
        namespaces=(
            CanonicalNamespace(
                id=ns_id,
                name="public",
                tables=tuple(tables),
                provenance=make_dep_provenance(engine=engine, identifier="public"),
            ),
        ),
        provenance=make_dep_provenance(engine=engine, identifier="linear_db"),
    )


def make_diamond_dag_schema(
    engine: str = "postgresql",
    workspace_id: str | None = "test-ws",
) -> CanonicalDatabase:
    """Creates a diamond DAG: root <- (branch_a, branch_b) <- sink."""
    db_id = compute_stable_object_id(
        engine=engine,
        object_kind=ObjectKind.DATABASE,
        native_name="diamond_db",
        workspace_id=workspace_id,
    )
    ns_id = compute_stable_object_id(
        engine=engine,
        object_kind=ObjectKind.NAMESPACE,
        native_name="public",
        parent_id=db_id,
        workspace_id=workspace_id,
    )

    root_id = compute_stable_object_id(
        engine=engine,
        object_kind=ObjectKind.TABLE,
        native_name="root",
        parent_id=ns_id,
        workspace_id=workspace_id,
    )
    root_table = CanonicalTable(
        id=root_id,
        namespace_id=ns_id,
        name="root",
        schema_name="public",
        columns=(make_col(root_id, "id", 1, engine=engine, workspace_id=workspace_id),),
        provenance=make_dep_provenance(engine=engine),
    )

    a_id = compute_stable_object_id(
        engine=engine,
        object_kind=ObjectKind.TABLE,
        native_name="branch_a",
        parent_id=ns_id,
        workspace_id=workspace_id,
    )
    fk_a = CanonicalForeignKey(
        id=compute_stable_object_id(
            engine=engine,
            object_kind=ObjectKind.FOREIGN_KEY,
            native_name="fk_a_root",
            parent_id=a_id,
            workspace_id=workspace_id,
        ),
        table_id=a_id,
        name="fk_a_root",
        column_names=("root_id",),
        referenced_table_id=root_id,
        referenced_schema_name="public",
        referenced_table_name="root",
        referenced_column_names=("id",),
        provenance=make_dep_provenance(engine=engine),
    )
    a_table = CanonicalTable(
        id=a_id,
        namespace_id=ns_id,
        name="branch_a",
        schema_name="public",
        columns=(
            make_col(a_id, "id", 1, engine=engine, workspace_id=workspace_id),
            make_col(a_id, "root_id", 2, engine=engine, workspace_id=workspace_id),
        ),
        foreign_keys=(fk_a,),
        provenance=make_dep_provenance(engine=engine),
    )

    b_id = compute_stable_object_id(
        engine=engine,
        object_kind=ObjectKind.TABLE,
        native_name="branch_b",
        parent_id=ns_id,
        workspace_id=workspace_id,
    )
    fk_b = CanonicalForeignKey(
        id=compute_stable_object_id(
            engine=engine,
            object_kind=ObjectKind.FOREIGN_KEY,
            native_name="fk_b_root",
            parent_id=b_id,
            workspace_id=workspace_id,
        ),
        table_id=b_id,
        name="fk_b_root",
        column_names=("root_id",),
        referenced_table_id=root_id,
        referenced_schema_name="public",
        referenced_table_name="root",
        referenced_column_names=("id",),
        provenance=make_dep_provenance(engine=engine),
    )
    b_table = CanonicalTable(
        id=b_id,
        namespace_id=ns_id,
        name="branch_b",
        schema_name="public",
        columns=(
            make_col(b_id, "id", 1, engine=engine, workspace_id=workspace_id),
            make_col(b_id, "root_id", 2, engine=engine, workspace_id=workspace_id),
        ),
        foreign_keys=(fk_b,),
        provenance=make_dep_provenance(engine=engine),
    )

    sink_id = compute_stable_object_id(
        engine=engine,
        object_kind=ObjectKind.TABLE,
        native_name="sink",
        parent_id=ns_id,
        workspace_id=workspace_id,
    )
    fk_sink_a = CanonicalForeignKey(
        id=compute_stable_object_id(
            engine=engine,
            object_kind=ObjectKind.FOREIGN_KEY,
            native_name="fk_sink_a",
            parent_id=sink_id,
            workspace_id=workspace_id,
        ),
        table_id=sink_id,
        name="fk_sink_a",
        column_names=("branch_a_id",),
        referenced_table_id=a_id,
        referenced_schema_name="public",
        referenced_table_name="branch_a",
        referenced_column_names=("id",),
        provenance=make_dep_provenance(engine=engine),
    )
    fk_sink_b = CanonicalForeignKey(
        id=compute_stable_object_id(
            engine=engine,
            object_kind=ObjectKind.FOREIGN_KEY,
            native_name="fk_sink_b",
            parent_id=sink_id,
            workspace_id=workspace_id,
        ),
        table_id=sink_id,
        name="fk_sink_b",
        column_names=("branch_b_id",),
        referenced_table_id=b_id,
        referenced_schema_name="public",
        referenced_table_name="branch_b",
        referenced_column_names=("id",),
        provenance=make_dep_provenance(engine=engine),
    )
    sink_table = CanonicalTable(
        id=sink_id,
        namespace_id=ns_id,
        name="sink",
        schema_name="public",
        columns=(
            make_col(sink_id, "id", 1, engine=engine, workspace_id=workspace_id),
            make_col(sink_id, "branch_a_id", 2, engine=engine, workspace_id=workspace_id),
            make_col(sink_id, "branch_b_id", 3, engine=engine, workspace_id=workspace_id),
        ),
        foreign_keys=(fk_sink_a, fk_sink_b),
        provenance=make_dep_provenance(engine=engine),
    )

    return CanonicalDatabase(
        id=db_id,
        name="diamond_db",
        engine=engine,
        namespaces=(
            CanonicalNamespace(
                id=ns_id,
                name="public",
                tables=(root_table, a_table, b_table, sink_table),
                provenance=make_dep_provenance(engine=engine),
            ),
        ),
        provenance=make_dep_provenance(engine=engine),
    )


def make_self_referencing_schema(
    engine: str = "postgresql",
    is_nullable: bool = True,
    workspace_id: str | None = "test-ws",
) -> CanonicalDatabase:
    """Creates a self-referencing table: employees.manager_id -> employees.id."""
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
    tid = compute_stable_object_id(
        engine=engine,
        object_kind=ObjectKind.TABLE,
        native_name="employees",
        parent_id=ns_id,
        workspace_id=workspace_id,
    )

    id_col = make_col(tid, "id", 1, is_nullable=False, engine=engine, workspace_id=workspace_id)
    mgr_col = make_col(
        tid, "manager_id", 2, is_nullable=is_nullable, engine=engine, workspace_id=workspace_id
    )
    fk = CanonicalForeignKey(
        id=compute_stable_object_id(
            engine=engine,
            object_kind=ObjectKind.FOREIGN_KEY,
            native_name="fk_emp_mgr",
            parent_id=tid,
            workspace_id=workspace_id,
        ),
        table_id=tid,
        name="fk_emp_mgr",
        column_names=("manager_id",),
        referenced_table_id=tid,
        referenced_schema_name="public",
        referenced_table_name="employees",
        referenced_column_names=("id",),
        provenance=make_dep_provenance(engine=engine),
    )
    table = CanonicalTable(
        id=tid,
        namespace_id=ns_id,
        name="employees",
        schema_name="public",
        columns=(id_col, mgr_col),
        foreign_keys=(fk,),
        provenance=make_dep_provenance(engine=engine),
    )

    return CanonicalDatabase(
        id=db_id,
        name="self_db",
        engine=engine,
        namespaces=(
            CanonicalNamespace(
                id=ns_id,
                name="public",
                tables=(table,),
                provenance=make_dep_provenance(engine=engine),
            ),
        ),
        provenance=make_dep_provenance(engine=engine),
    )


def make_mutual_cycle_schema(
    engine: str = "postgresql",
    author_nullable: bool = True,
    book_nullable: bool = False,
    is_deferrable: bool = False,
    workspace_id: str | None = "test-ws",
) -> CanonicalDatabase:
    """Creates 2 mutually dependent tables: authors <-> books."""
    db_id = compute_stable_object_id(
        engine=engine,
        object_kind=ObjectKind.DATABASE,
        native_name="mutual_db",
        workspace_id=workspace_id,
    )
    ns_id = compute_stable_object_id(
        engine=engine,
        object_kind=ObjectKind.NAMESPACE,
        native_name="public",
        parent_id=db_id,
        workspace_id=workspace_id,
    )
    a_tid = compute_stable_object_id(
        engine=engine,
        object_kind=ObjectKind.TABLE,
        native_name="authors",
        parent_id=ns_id,
        workspace_id=workspace_id,
    )
    b_tid = compute_stable_object_id(
        engine=engine,
        object_kind=ObjectKind.TABLE,
        native_name="books",
        parent_id=ns_id,
        workspace_id=workspace_id,
    )

    a_id = make_col(a_tid, "id", 1, is_nullable=False, engine=engine, workspace_id=workspace_id)
    a_best = make_col(
        a_tid,
        "best_book_id",
        2,
        is_nullable=author_nullable,
        engine=engine,
        workspace_id=workspace_id,
    )
    b_id = make_col(b_tid, "id", 1, is_nullable=False, engine=engine, workspace_id=workspace_id)
    b_auth = make_col(
        b_tid, "author_id", 2, is_nullable=book_nullable, engine=engine, workspace_id=workspace_id
    )

    fk_a = CanonicalForeignKey(
        id=compute_stable_object_id(
            engine=engine,
            object_kind=ObjectKind.FOREIGN_KEY,
            native_name="fk_authors_book",
            parent_id=a_tid,
            workspace_id=workspace_id,
        ),
        table_id=a_tid,
        name="fk_authors_book",
        column_names=("best_book_id",),
        referenced_table_id=b_tid,
        referenced_schema_name="public",
        referenced_table_name="books",
        referenced_column_names=("id",),
        is_deferrable=is_deferrable,
        provenance=make_dep_provenance(engine=engine),
    )
    fk_b = CanonicalForeignKey(
        id=compute_stable_object_id(
            engine=engine,
            object_kind=ObjectKind.FOREIGN_KEY,
            native_name="fk_books_author",
            parent_id=b_tid,
            workspace_id=workspace_id,
        ),
        table_id=b_tid,
        name="fk_books_author",
        column_names=("author_id",),
        referenced_table_id=a_tid,
        referenced_schema_name="public",
        referenced_table_name="authors",
        referenced_column_names=("id",),
        is_deferrable=is_deferrable,
        provenance=make_dep_provenance(engine=engine),
    )

    a_table = CanonicalTable(
        id=a_tid,
        namespace_id=ns_id,
        name="authors",
        schema_name="public",
        columns=(a_id, a_best),
        foreign_keys=(fk_a,),
        provenance=make_dep_provenance(engine=engine),
    )
    b_table = CanonicalTable(
        id=b_tid,
        namespace_id=ns_id,
        name="books",
        schema_name="public",
        columns=(b_id, b_auth),
        foreign_keys=(fk_b,),
        provenance=make_dep_provenance(engine=engine),
    )

    return CanonicalDatabase(
        id=db_id,
        name="mutual_db",
        engine=engine,
        namespaces=(
            CanonicalNamespace(
                id=ns_id,
                name="public",
                tables=(a_table, b_table),
                provenance=make_dep_provenance(engine=engine),
            ),
        ),
        provenance=make_dep_provenance(engine=engine),
    )


def make_indirect_cycle_schema(
    engine: str = "postgresql",
    workspace_id: str | None = "test-ws",
) -> CanonicalDatabase:
    """Creates a 3-table circular dependency: tA -> tB -> tC -> tA."""
    db_id = compute_stable_object_id(
        engine=engine,
        object_kind=ObjectKind.DATABASE,
        native_name="indirect_db",
        workspace_id=workspace_id,
    )
    ns_id = compute_stable_object_id(
        engine=engine,
        object_kind=ObjectKind.NAMESPACE,
        native_name="public",
        parent_id=db_id,
        workspace_id=workspace_id,
    )

    names = ["tA", "tB", "tC"]
    tids = [
        compute_stable_object_id(
            engine=engine,
            object_kind=ObjectKind.TABLE,
            native_name=n,
            parent_id=ns_id,
            workspace_id=workspace_id,
        )
        for n in names
    ]

    tables: list[CanonicalTable] = []
    for i in range(3):
        src_name = names[i]
        src_tid = tids[i]
        tgt_name = names[(i + 1) % 3]
        tgt_tid = tids[(i + 1) % 3]

        id_col = make_col(src_tid, "id", 1, engine=engine, workspace_id=workspace_id)
        ref_col = make_col(
            src_tid, f"{tgt_name}_id", 2, is_nullable=True, engine=engine, workspace_id=workspace_id
        )
        fk = CanonicalForeignKey(
            id=compute_stable_object_id(
                engine=engine,
                object_kind=ObjectKind.FOREIGN_KEY,
                native_name=f"fk_{src_name}_{tgt_name}",
                parent_id=src_tid,
                workspace_id=workspace_id,
            ),
            table_id=src_tid,
            name=f"fk_{src_name}_{tgt_name}",
            column_names=(f"{tgt_name}_id",),
            referenced_table_id=tgt_tid,
            referenced_schema_name="public",
            referenced_table_name=tgt_name,
            referenced_column_names=("id",),
            provenance=make_dep_provenance(engine=engine),
        )
        tables.append(
            CanonicalTable(
                id=src_tid,
                namespace_id=ns_id,
                name=src_name,
                schema_name="public",
                columns=(id_col, ref_col),
                foreign_keys=(fk,),
                provenance=make_dep_provenance(engine=engine),
            )
        )

    return CanonicalDatabase(
        id=db_id,
        name="indirect_db",
        engine=engine,
        namespaces=(
            CanonicalNamespace(
                id=ns_id,
                name="public",
                tables=tuple(tables),
                provenance=make_dep_provenance(engine=engine),
            ),
        ),
        provenance=make_dep_provenance(engine=engine),
    )


def make_complex_scc_schema(
    engine: str = "postgresql",
    workspace_id: str | None = "test-ws",
) -> CanonicalDatabase:
    """Creates a complex multi-cycle intertwined SCC: (A, B, C, D)."""
    db_id = compute_stable_object_id(
        engine=engine,
        object_kind=ObjectKind.DATABASE,
        native_name="complex_db",
        workspace_id=workspace_id,
    )
    ns_id = compute_stable_object_id(
        engine=engine,
        object_kind=ObjectKind.NAMESPACE,
        native_name="public",
        parent_id=db_id,
        workspace_id=workspace_id,
    )

    names = ["node_a", "node_b", "node_c", "node_d"]
    tids = {
        n: compute_stable_object_id(
            engine=engine,
            object_kind=ObjectKind.TABLE,
            native_name=n,
            parent_id=ns_id,
            workspace_id=workspace_id,
        )
        for n in names
    }

    # Edges:
    # a -> b, b -> c, c -> a
    # b -> d, d -> b
    edge_defs = [
        ("node_a", "node_b"),
        ("node_b", "node_c"),
        ("node_c", "node_a"),
        ("node_b", "node_d"),
        ("node_d", "node_b"),
    ]

    fks_by_table: dict[str, list[CanonicalForeignKey]] = {n: [] for n in names}
    cols_by_table: dict[str, list[CanonicalColumn]] = {
        n: [make_col(tids[n], "id", 1, engine=engine, workspace_id=workspace_id)] for n in names
    }

    for idx, (src, tgt) in enumerate(edge_defs):
        src_tid = tids[src]
        tgt_tid = tids[tgt]
        ref_col = make_col(
            src_tid,
            f"ref_{tgt}_{idx}",
            len(cols_by_table[src]) + 1,
            is_nullable=True,
            engine=engine,
            workspace_id=workspace_id,
        )
        cols_by_table[src].append(ref_col)
        fk = CanonicalForeignKey(
            id=compute_stable_object_id(
                engine=engine,
                object_kind=ObjectKind.FOREIGN_KEY,
                native_name=f"fk_{src}_{tgt}_{idx}",
                parent_id=src_tid,
                workspace_id=workspace_id,
            ),
            table_id=src_tid,
            name=f"fk_{src}_{tgt}_{idx}",
            column_names=(ref_col.name,),
            referenced_table_id=tgt_tid,
            referenced_schema_name="public",
            referenced_table_name=tgt,
            referenced_column_names=("id",),
            provenance=make_dep_provenance(engine=engine),
        )
        fks_by_table[src].append(fk)

    tables = [
        CanonicalTable(
            id=tids[n],
            namespace_id=ns_id,
            name=n,
            schema_name="public",
            columns=tuple(cols_by_table[n]),
            foreign_keys=tuple(fks_by_table[n]),
            provenance=make_dep_provenance(engine=engine),
        )
        for n in names
    ]

    return CanonicalDatabase(
        id=db_id,
        name="complex_db",
        engine=engine,
        namespaces=(
            CanonicalNamespace(
                id=ns_id,
                name="public",
                tables=tuple(tables),
                provenance=make_dep_provenance(engine=engine),
            ),
        ),
        provenance=make_dep_provenance(engine=engine),
    )


def make_ecommerce_schema(
    engine: str = "postgresql",
    workspace_id: str | None = "test-ws",
) -> CanonicalDatabase:
    """Creates a production-style 7-table e-commerce schema with roots, branches, and leaves."""
    db_id = compute_stable_object_id(
        engine=engine,
        object_kind=ObjectKind.DATABASE,
        native_name="ecommerce_db",
        workspace_id=workspace_id,
    )
    ns_id = compute_stable_object_id(
        engine=engine,
        object_kind=ObjectKind.NAMESPACE,
        native_name="public",
        parent_id=db_id,
        workspace_id=workspace_id,
    )

    names = ["users", "categories", "products", "orders", "order_items", "reviews", "audit_log"]
    tids = {
        n: compute_stable_object_id(
            engine=engine,
            object_kind=ObjectKind.TABLE,
            native_name=n,
            parent_id=ns_id,
            workspace_id=workspace_id,
        )
        for n in names
    }

    # users (root)
    users_tbl = CanonicalTable(
        id=tids["users"],
        namespace_id=ns_id,
        name="users",
        schema_name="public",
        columns=(make_col(tids["users"], "id", 1, engine=engine, workspace_id=workspace_id),),
        provenance=make_dep_provenance(engine=engine),
    )

    # categories (root)
    cat_tbl = CanonicalTable(
        id=tids["categories"],
        namespace_id=ns_id,
        name="categories",
        schema_name="public",
        columns=(make_col(tids["categories"], "id", 1, engine=engine, workspace_id=workspace_id),),
        provenance=make_dep_provenance(engine=engine),
    )

    # audit_log (isolated)
    audit_tbl = CanonicalTable(
        id=tids["audit_log"],
        namespace_id=ns_id,
        name="audit_log",
        schema_name="public",
        columns=(make_col(tids["audit_log"], "id", 1, engine=engine, workspace_id=workspace_id),),
        provenance=make_dep_provenance(engine=engine),
    )

    # products -> categories
    fk_prod_cat = CanonicalForeignKey(
        id=compute_stable_object_id(
            engine=engine,
            object_kind=ObjectKind.FOREIGN_KEY,
            native_name="fk_prod_cat",
            parent_id=tids["products"],
            workspace_id=workspace_id,
        ),
        table_id=tids["products"],
        name="fk_prod_cat",
        column_names=("category_id",),
        referenced_table_id=tids["categories"],
        referenced_schema_name="public",
        referenced_table_name="categories",
        referenced_column_names=("id",),
        provenance=make_dep_provenance(engine=engine),
    )
    prod_tbl = CanonicalTable(
        id=tids["products"],
        namespace_id=ns_id,
        name="products",
        schema_name="public",
        columns=(
            make_col(tids["products"], "id", 1, engine=engine, workspace_id=workspace_id),
            make_col(tids["products"], "category_id", 2, engine=engine, workspace_id=workspace_id),
        ),
        foreign_keys=(fk_prod_cat,),
        provenance=make_dep_provenance(engine=engine),
    )

    # orders -> users
    fk_ord_usr = CanonicalForeignKey(
        id=compute_stable_object_id(
            engine=engine,
            object_kind=ObjectKind.FOREIGN_KEY,
            native_name="fk_ord_usr",
            parent_id=tids["orders"],
            workspace_id=workspace_id,
        ),
        table_id=tids["orders"],
        name="fk_ord_usr",
        column_names=("user_id",),
        referenced_table_id=tids["users"],
        referenced_schema_name="public",
        referenced_table_name="users",
        referenced_column_names=("id",),
        provenance=make_dep_provenance(engine=engine),
    )
    ord_tbl = CanonicalTable(
        id=tids["orders"],
        namespace_id=ns_id,
        name="orders",
        schema_name="public",
        columns=(
            make_col(tids["orders"], "id", 1, engine=engine, workspace_id=workspace_id),
            make_col(tids["orders"], "user_id", 2, engine=engine, workspace_id=workspace_id),
        ),
        foreign_keys=(fk_ord_usr,),
        provenance=make_dep_provenance(engine=engine),
    )

    # order_items -> orders and products
    fk_oi_ord = CanonicalForeignKey(
        id=compute_stable_object_id(
            engine=engine,
            object_kind=ObjectKind.FOREIGN_KEY,
            native_name="fk_oi_ord",
            parent_id=tids["order_items"],
            workspace_id=workspace_id,
        ),
        table_id=tids["order_items"],
        name="fk_oi_ord",
        column_names=("order_id",),
        referenced_table_id=tids["orders"],
        referenced_schema_name="public",
        referenced_table_name="orders",
        referenced_column_names=("id",),
        provenance=make_dep_provenance(engine=engine),
    )
    fk_oi_prod = CanonicalForeignKey(
        id=compute_stable_object_id(
            engine=engine,
            object_kind=ObjectKind.FOREIGN_KEY,
            native_name="fk_oi_prod",
            parent_id=tids["order_items"],
            workspace_id=workspace_id,
        ),
        table_id=tids["order_items"],
        name="fk_oi_prod",
        column_names=("product_id",),
        referenced_table_id=tids["products"],
        referenced_schema_name="public",
        referenced_table_name="products",
        referenced_column_names=("id",),
        provenance=make_dep_provenance(engine=engine),
    )
    oi_tbl = CanonicalTable(
        id=tids["order_items"],
        namespace_id=ns_id,
        name="order_items",
        schema_name="public",
        columns=(
            make_col(tids["order_items"], "id", 1, engine=engine, workspace_id=workspace_id),
            make_col(tids["order_items"], "order_id", 2, engine=engine, workspace_id=workspace_id),
            make_col(
                tids["order_items"], "product_id", 3, engine=engine, workspace_id=workspace_id
            ),
        ),
        foreign_keys=(fk_oi_ord, fk_oi_prod),
        provenance=make_dep_provenance(engine=engine),
    )

    # reviews -> users and products
    fk_rev_usr = CanonicalForeignKey(
        id=compute_stable_object_id(
            engine=engine,
            object_kind=ObjectKind.FOREIGN_KEY,
            native_name="fk_rev_usr",
            parent_id=tids["reviews"],
            workspace_id=workspace_id,
        ),
        table_id=tids["reviews"],
        name="fk_rev_usr",
        column_names=("user_id",),
        referenced_table_id=tids["users"],
        referenced_schema_name="public",
        referenced_table_name="users",
        referenced_column_names=("id",),
        provenance=make_dep_provenance(engine=engine),
    )
    fk_rev_prod = CanonicalForeignKey(
        id=compute_stable_object_id(
            engine=engine,
            object_kind=ObjectKind.FOREIGN_KEY,
            native_name="fk_rev_prod",
            parent_id=tids["reviews"],
            workspace_id=workspace_id,
        ),
        table_id=tids["reviews"],
        name="fk_rev_prod",
        column_names=("product_id",),
        referenced_table_id=tids["products"],
        referenced_schema_name="public",
        referenced_table_name="products",
        referenced_column_names=("id",),
        provenance=make_dep_provenance(engine=engine),
    )
    rev_tbl = CanonicalTable(
        id=tids["reviews"],
        namespace_id=ns_id,
        name="reviews",
        schema_name="public",
        columns=(
            make_col(tids["reviews"], "id", 1, engine=engine, workspace_id=workspace_id),
            make_col(tids["reviews"], "user_id", 2, engine=engine, workspace_id=workspace_id),
            make_col(tids["reviews"], "product_id", 3, engine=engine, workspace_id=workspace_id),
        ),
        foreign_keys=(fk_rev_usr, fk_rev_prod),
        provenance=make_dep_provenance(engine=engine),
    )

    all_tables = (users_tbl, cat_tbl, prod_tbl, ord_tbl, oi_tbl, rev_tbl, audit_tbl)

    return CanonicalDatabase(
        id=db_id,
        name="ecommerce_db",
        engine=engine,
        namespaces=(
            CanonicalNamespace(
                id=ns_id,
                name="public",
                tables=all_tables,
                provenance=make_dep_provenance(engine=engine),
            ),
        ),
        provenance=make_dep_provenance(engine=engine),
    )


def analyze_database(db: CanonicalDatabase) -> DependencyAnalysisResult:
    """Helper to construct ForeignKeyGraph and run DependencyAnalyzer."""
    from dera.reverse_engineering.builder import SchemaBuilder

    schema = SchemaBuilder.from_canonical_database(db)
    graph = ForeignKeyGraphBuilder.from_schema(schema)
    analyzer = DependencyAnalyzer()
    return analyzer.analyze(graph, schema=schema)
