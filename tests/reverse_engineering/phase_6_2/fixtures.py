"""Deterministic test fixtures for Phase 6.2 Structural Reconstruction.

Provides multi-engine, composite key, generated column, inert default, and
constraint fixtures across PostgreSQL, SQLite, MySQL, and MariaDB.
"""

from datetime import datetime, timezone
from typing import Any

from dera.metadata.enums import (
    CanonicalTypeCategory,
    ConstraintType,
    ForeignKeyAction,
    GenerationMode,
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
from dera.metadata.provenance import ProvenanceRecord
from dera.reverse_engineering.schema import SchemaRepresentation


def make_test_provenance(engine: str = "postgresql") -> ProvenanceRecord:
    """Create a deterministic test provenance record."""
    return ProvenanceRecord(
        source_engine=engine,
        source_version="16.0",
        connector_version="1.0.0",
        extracted_at=datetime(2026, 10, 27, 12, 0, 0, tzinfo=timezone.utc),
        completeness=MetadataCompleteness.COMPLETE,
        location="localhost:5432/test_db",
    )


def make_test_column(
    table_id: str,
    name: str,
    ordinal: int,
    native_type: str = "integer",
    canonical_type: CanonicalTypeCategory = CanonicalTypeCategory.INTEGER,
    is_nullable: bool | None = False,
    default_val: str | None = None,
    is_generated: bool = False,
    gen_expr: str | None = None,
    extra: dict[str, Any] | None = None,
    engine: str = "postgresql",
    workspace_id: str | None = "test-ws",
) -> CanonicalColumn:
    """Create a CanonicalColumn with deterministic ObjectId."""
    col_id = compute_stable_object_id(
        kind=ObjectKind.COLUMN,
        engine=engine,
        components=(table_id, name),
        workspace_id=workspace_id,
    )
    is_ident = bool(extra.get("is_identity", False)) if extra else False
    return CanonicalColumn(
        id=col_id,
        table_id=table_id,
        name=name,
        ordinal_position=ordinal,
        native_type=native_type,
        canonical_type=canonical_type,
        is_nullable=is_nullable,
        default_value=default_val,
        is_identity=is_ident,
        is_generated=is_generated,
        generation_expression=gen_expr,
        generation_mode=GenerationMode.STORED if is_generated else GenerationMode.NONE,
        extra_metadata=extra or {},
        provenance=make_test_provenance(engine),
    )


def build_postgres_enterprise_fixture(workspace_id: str = "ws-ent") -> CanonicalDatabase:
    """Construct an enterprise PostgreSQL schema with composite PK, composite FK, generated column, and CHECKs."""
    engine = "postgresql"
    prov = make_test_provenance(engine)
    db_id = compute_stable_object_id(ObjectKind.DATABASE, engine, ("enterprise_db",), workspace_id)
    ns_id = compute_stable_object_id(ObjectKind.NAMESPACE, engine, ("public",), workspace_id)

    # 1. Customers Table
    cust_id = compute_stable_object_id(ObjectKind.TABLE, engine, ("public", "customers"), workspace_id)
    cust_col_tenant = make_test_column(str(cust_id), "tenant_id", 1, "uuid", CanonicalTypeCategory.UUID, False, workspace_id=workspace_id)
    cust_col_id = make_test_column(str(cust_id), "id", 2, "bigint", CanonicalTypeCategory.INTEGER, False, workspace_id=workspace_id)
    cust_col_name = make_test_column(str(cust_id), "name", 3, "varchar(255)", CanonicalTypeCategory.TEXT, False, workspace_id=workspace_id)
    cust_col_email = make_test_column(str(cust_id), "email", 4, "varchar(255)", CanonicalTypeCategory.TEXT, False, workspace_id=workspace_id)

    cust_pk_id = compute_stable_object_id(ObjectKind.PRIMARY_KEY, engine, (str(cust_id), "pk_customers"), workspace_id)
    cust_pk = CanonicalConstraint(
        id=cust_pk_id,
        table_id=cust_id,
        name="pk_customers",
        constraint_type=ConstraintType.PRIMARY_KEY,
        columns=("tenant_id", "id"),
        column_ids=(cust_col_tenant.id, cust_col_id.id),
        provenance=prov,
    )

    cust_uq_id = compute_stable_object_id(ObjectKind.UNIQUE_CONSTRAINT, engine, (str(cust_id), "uq_customers_tenant_email"), workspace_id)
    cust_uq = CanonicalConstraint(
        id=cust_uq_id,
        table_id=cust_id,
        name="uq_customers_tenant_email",
        constraint_type=ConstraintType.UNIQUE,
        columns=("tenant_id", "email"),
        column_ids=(cust_col_tenant.id, cust_col_email.id),
        provenance=prov,
    )

    customers_table = CanonicalTable(
        id=cust_id,
        namespace_id=ns_id,
        schema_name="public",
        name="customers",
        table_type=TableType.TABLE,
        columns=(cust_col_tenant, cust_col_id, cust_col_name, cust_col_email),
        primary_key=cust_pk,
        constraints=(cust_uq,),
        foreign_keys=(),
        provenance=prov,
    )

    # 2. Orders Table (Composite PK: tenant_id, order_id; Composite FK -> customers)
    orders_id = compute_stable_object_id(ObjectKind.TABLE, engine, ("public", "orders"), workspace_id)
    ord_col_tenant = make_test_column(str(orders_id), "tenant_id", 1, "uuid", CanonicalTypeCategory.UUID, False, workspace_id=workspace_id)
    ord_col_order_id = make_test_column(str(orders_id), "order_id", 2, "bigint", CanonicalTypeCategory.INTEGER, False, workspace_id=workspace_id)
    ord_col_cust_id = make_test_column(str(orders_id), "customer_id", 3, "bigint", CanonicalTypeCategory.INTEGER, False, workspace_id=workspace_id)
    ord_col_subtotal = make_test_column(str(orders_id), "subtotal", 4, "numeric(10,2)", CanonicalTypeCategory.DECIMAL, False, "0.00", workspace_id=workspace_id)
    ord_col_tax = make_test_column(str(orders_id), "tax", 5, "numeric(10,2)", CanonicalTypeCategory.DECIMAL, False, "0.00", workspace_id=workspace_id)
    ord_col_total = make_test_column(
        str(orders_id),
        "total",
        6,
        "numeric(10,2)",
        CanonicalTypeCategory.DECIMAL,
        False,
        is_generated=True,
        gen_expr="subtotal + tax",
        workspace_id=workspace_id,
    )

    ord_pk_id = compute_stable_object_id(ObjectKind.PRIMARY_KEY, engine, (str(orders_id), "pk_orders"), workspace_id)
    ord_pk = CanonicalConstraint(
        id=ord_pk_id,
        table_id=orders_id,
        name="pk_orders",
        constraint_type=ConstraintType.PRIMARY_KEY,
        columns=("tenant_id", "order_id"),
        column_ids=(ord_col_tenant.id, ord_col_order_id.id),
        provenance=prov,
    )

    ord_fk_id = compute_stable_object_id(ObjectKind.FOREIGN_KEY, engine, (str(orders_id), "fk_orders_customer"), workspace_id)
    ord_fk = CanonicalForeignKey(
        id=ord_fk_id,
        table_id=orders_id,
        name="fk_orders_customer",
        columns=("tenant_id", "customer_id"),
        column_ids=(ord_col_tenant.id, ord_col_cust_id.id),
        referenced_table_id=cust_id,
        referenced_schema="public",
        referenced_table="customers",
        referenced_columns=("tenant_id", "id"),
        referenced_column_ids=(cust_col_tenant.id, cust_col_id.id),
        on_update=ForeignKeyAction.CASCADE,
        on_delete=ForeignKeyAction.RESTRICT,
        provenance=prov,
    )

    ord_ck_id = compute_stable_object_id(ObjectKind.CHECK_CONSTRAINT, engine, (str(orders_id), "ck_orders_subtotal_positive"), workspace_id)
    ord_ck = CanonicalConstraint(
        id=ord_ck_id,
        table_id=orders_id,
        name="ck_orders_subtotal_positive",
        constraint_type=ConstraintType.CHECK,
        expression="subtotal >= 0",
        provenance=prov,
    )

    orders_table = CanonicalTable(
        id=orders_id,
        namespace_id=ns_id,
        schema_name="public",
        name="orders",
        table_type=TableType.TABLE,
        columns=(ord_col_tenant, ord_col_order_id, ord_col_cust_id, ord_col_subtotal, ord_col_tax, ord_col_total),
        primary_key=ord_pk,
        constraints=(ord_ck,),
        foreign_keys=(ord_fk,),
        provenance=prov,
    )

    namespace = CanonicalNamespace(
        id=ns_id,
        database_id=db_id,
        name="public",
        tables=(customers_table, orders_table),
        provenance=prov,
    )

    return CanonicalDatabase(
        id=db_id,
        name="enterprise_db",
        engine=engine,
        version="16.0",
        workspace_id=workspace_id,
        namespaces=(namespace,),
        provenance=prov,
    )


def build_sqlite_fixture(workspace_id: str = "ws-sqlite") -> CanonicalDatabase:
    """Construct an SQLite schema with STRICT, WITHOUT ROWID, and composite primary key."""
    engine = "sqlite"
    prov = make_test_provenance(engine)
    db_id = compute_stable_object_id(ObjectKind.DATABASE, engine, ("main",), workspace_id)
    ns_id = compute_stable_object_id(ObjectKind.NAMESPACE, engine, ("main",), workspace_id)

    tbl_id = compute_stable_object_id(ObjectKind.TABLE, engine, ("main", "inventory"), workspace_id)
    col_warehouse = make_test_column(str(tbl_id), "warehouse_id", 1, "INTEGER", CanonicalTypeCategory.INTEGER, False, engine=engine, workspace_id=workspace_id)
    col_sku = make_test_column(str(tbl_id), "sku", 2, "TEXT", CanonicalTypeCategory.TEXT, False, engine=engine, workspace_id=workspace_id)
    col_qty = make_test_column(str(tbl_id), "quantity", 3, "INTEGER", CanonicalTypeCategory.INTEGER, False, "0", engine=engine, workspace_id=workspace_id)

    pk_id = compute_stable_object_id(ObjectKind.PRIMARY_KEY, engine, (str(tbl_id), "pk_inventory"), workspace_id)
    pk = CanonicalConstraint(
        id=pk_id,
        table_id=tbl_id,
        name="pk_inventory",
        constraint_type=ConstraintType.PRIMARY_KEY,
        columns=("warehouse_id", "sku"),
        column_ids=(col_warehouse.id, col_sku.id),
        provenance=prov,
    )

    ck_id = compute_stable_object_id(ObjectKind.CHECK_CONSTRAINT, engine, (str(tbl_id), "ck_quantity_non_negative"), workspace_id)
    ck = CanonicalConstraint(
        id=ck_id,
        table_id=tbl_id,
        name="ck_quantity_non_negative",
        constraint_type=ConstraintType.CHECK,
        expression="quantity >= 0",
        provenance=prov,
    )

    tbl = CanonicalTable(
        id=tbl_id,
        namespace_id=ns_id,
        schema_name="main",
        name="inventory",
        table_type=TableType.TABLE,
        columns=(col_warehouse, col_sku, col_qty),
        primary_key=pk,
        constraints=(ck,),
        extra_metadata={"without_rowid": True, "is_strict": True},
        provenance=prov,
    )

    ns = CanonicalNamespace(id=ns_id, database_id=db_id, name="main", tables=(tbl,), provenance=prov)
    return CanonicalDatabase(id=db_id, name="main", engine=engine, version="3.45.0", workspace_id=workspace_id, namespaces=(ns,), provenance=prov)


def build_mysql_fixture(workspace_id: str = "ws-mysql") -> CanonicalDatabase:
    """Construct a MySQL schema with AUTO_INCREMENT, ENUM, and storage engine attributes."""
    engine = "mysql"
    prov = make_test_provenance(engine)
    db_id = compute_stable_object_id(ObjectKind.DATABASE, engine, ("shop_db",), workspace_id)
    ns_id = compute_stable_object_id(ObjectKind.NAMESPACE, engine, ("shop_db",), workspace_id)

    tbl_id = compute_stable_object_id(ObjectKind.TABLE, engine, ("shop_db", "products"), workspace_id)
    col_id = make_test_column(
        str(tbl_id),
        "id",
        1,
        "int unsigned",
        CanonicalTypeCategory.INTEGER,
        False,
        extra={"is_auto_increment": True, "extra": "auto_increment"},
        engine=engine,
        workspace_id=workspace_id,
    )
    col_name = make_test_column(str(tbl_id), "name", 2, "varchar(100)", CanonicalTypeCategory.TEXT, False, engine=engine, workspace_id=workspace_id)
    col_status = make_test_column(
        str(tbl_id),
        "status",
        3,
        "enum('active','inactive','archived')",
        CanonicalTypeCategory.ENUM,
        False,
        "'active'",
        extra={"enum_values": ["active", "inactive", "archived"]},
        engine=engine,
        workspace_id=workspace_id,
    )

    pk_id = compute_stable_object_id(ObjectKind.PRIMARY_KEY, engine, (str(tbl_id), "PRIMARY"), workspace_id)
    pk = CanonicalConstraint(
        id=pk_id,
        table_id=tbl_id,
        name="PRIMARY",
        constraint_type=ConstraintType.PRIMARY_KEY,
        columns=("id",),
        column_ids=(col_id.id,),
        provenance=prov,
    )

    tbl = CanonicalTable(
        id=tbl_id,
        namespace_id=ns_id,
        schema_name="shop_db",
        name="products",
        table_type=TableType.TABLE,
        columns=(col_id, col_name, col_status),
        primary_key=pk,
        extra_metadata={"engine": "InnoDB", "row_format": "Dynamic", "collation": "utf8mb4_0900_ai_ci"},
        provenance=prov,
    )

    ns = CanonicalNamespace(id=ns_id, database_id=db_id, name="shop_db", tables=(tbl,), provenance=prov)
    return CanonicalDatabase(id=db_id, name="shop_db", engine=engine, version="8.0.36", workspace_id=workspace_id, namespaces=(ns,), provenance=prov)


def build_schema_representation_fixture(canonical_db: CanonicalDatabase) -> SchemaRepresentation:
    """Build a Phase 6.1 SchemaRepresentation from a CanonicalDatabase."""
    from dera.reverse_engineering.builder import SchemaBuilder

    return SchemaBuilder.from_canonical_database(canonical_db)
