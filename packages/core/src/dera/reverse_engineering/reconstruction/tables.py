"""Table reconstruction for Phase 6.2 Structural Reconstruction.

Coordinates the holistic synthesis of a table's ordered columns, primary key,
foreign keys, unique constraints, check constraints, native attributes, and
provenance into a strongly typed ReconstructedTable model.
"""

from dera.metadata.enums import ConstraintType, MetadataCompleteness, TableType
from dera.metadata.models import CanonicalTable
from dera.reverse_engineering.reconstruction.check_constraints import (
    reconstruct_check_constraints,
)
from dera.reverse_engineering.reconstruction.columns import reconstruct_columns
from dera.reverse_engineering.reconstruction.foreign_keys import reconstruct_foreign_keys
from dera.reverse_engineering.reconstruction.models import ReconstructedTable
from dera.reverse_engineering.reconstruction.primary_keys import reconstruct_primary_key
from dera.reverse_engineering.reconstruction.semantics import extract_table_native_attributes
from dera.reverse_engineering.reconstruction.unique_constraints import (
    reconstruct_unique_constraints,
)
from dera.reverse_engineering.registry import ObjectRegistry


def reconstruct_table(
    canonical_table: CanonicalTable,
    engine: str,
    registry: ObjectRegistry | None = None,
) -> ReconstructedTable:
    """Reconstruct a complete table definition from its canonical representation."""
    table_id = canonical_table.id
    schema_name = getattr(canonical_table, "schema_name", None)
    if (
        not schema_name
        and registry is not None
        and hasattr(canonical_table, "namespace_id")
        and registry.contains(canonical_table.namespace_id)
    ):
        ns = registry.get_namespace(canonical_table.namespace_id)
        schema_name = ns.name
    if not schema_name:
        schema_name = getattr(canonical_table, "namespace", "public")

    # 1. Reconstruct and order columns
    reconstructed_columns = reconstruct_columns(
        getattr(canonical_table, "columns", ()),
        parent_table_id=table_id,
        engine=engine,
    )

    # 2. Reconstruct primary key
    reconstructed_pk = reconstruct_primary_key(
        getattr(canonical_table, "primary_key", None),
        owning_table_id=table_id,
        columns=reconstructed_columns,
    )

    # 3. Reconstruct unique constraints
    uniques = getattr(canonical_table, "unique_constraints", None)
    if uniques is None:
        uniques = [
            c
            for c in getattr(canonical_table, "constraints", ())
            if getattr(c, "constraint_type", None) == ConstraintType.UNIQUE
        ]
    reconstructed_uniques = reconstruct_unique_constraints(
        uniques,
        owning_table_id=table_id,
        columns=reconstructed_columns,
    )

    # 4. Reconstruct foreign keys (with registry resolution if available)
    reconstructed_fks = reconstruct_foreign_keys(
        getattr(canonical_table, "foreign_keys", ()),
        source_table_id=table_id,
        source_namespace=schema_name,
        columns=reconstructed_columns,
        registry=registry,
    )

    # 5. Reconstruct check constraints
    checks = getattr(canonical_table, "check_constraints", None)
    if checks is None:
        checks = [
            c
            for c in getattr(canonical_table, "constraints", ())
            if getattr(c, "constraint_type", None) == ConstraintType.CHECK
        ]
    reconstructed_checks = reconstruct_check_constraints(
        checks,
        owning_table_id=table_id,
    )

    # 6. Extract dialect native attributes
    native_attrs = extract_table_native_attributes(canonical_table, engine)
    table_type = getattr(canonical_table, "table_type", None) or TableType.TABLE
    completeness = getattr(canonical_table, "completeness", None) or MetadataCompleteness.COMPLETE

    return ReconstructedTable(
        object_id=table_id,
        namespace=schema_name,
        native_name=canonical_table.name,
        table_type=table_type,
        columns=reconstructed_columns,
        primary_key=reconstructed_pk,
        foreign_keys=reconstructed_fks,
        unique_constraints=reconstructed_uniques,
        check_constraints=reconstructed_checks,
        native_attributes=native_attrs,
        completeness=completeness,
        provenance=canonical_table.provenance,
    )
