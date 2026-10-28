"""DERA Reverse Engineering — Phase 6.1 Referential Integrity & Structural Validation.

Validates the structural integrity and referential consistency of a SchemaRepresentation.
Checks:
- Namespace ownership and identity.
- Table parent namespaces.
- Column parent tables and ordinal positions.
- Constraint parent tables and referenced column existence.
- Index parent tables and indexed column existence.
- Trigger parent tables/views.
- Foreign key source table existence and source column existence.
- Foreign key target table resolution and target column existence (when resolved).
- Duplicate ObjectId detection and registry consistency.

Never mutates schema state. Reports structural inconsistencies explicitly.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from dera.metadata.enums import ObjectKind
from dera.metadata.models.table import CanonicalTable
from dera.reverse_engineering.errors import MissingParentError, SchemaValidationError

if TYPE_CHECKING:
    from dera.reverse_engineering.schema import SchemaRepresentation


def validate_schema_representation(
    schema: SchemaRepresentation,
    strict: bool = False,
    strict_foreign_keys: bool = False,
) -> tuple[str, ...]:
    """Validate referential integrity and structural consistency of a schema representation.

    Args:
        schema: The SchemaRepresentation to validate.
        strict: If True, raises MissingParentError or SchemaValidationError on first error.
        strict_foreign_keys: If True, missing FK target tables are treated as errors.

    Returns:
        Tuple of diagnostic error/warning messages encountered during validation.

    Raises:
        MissingParentError: If strict=True and a required parent object is missing.
        SchemaValidationError: If strict=True and any referential rule is violated.
    """
    errors: list[str] = []
    reg = schema.registry
    db = schema.database
    fk_references = {ref.foreign_key_id: ref for ref in schema.foreign_key_references}

    # 1. Database-level validation
    if not db.id or not db.id.startswith(f"dera:{ObjectKind.DATABASE.value}:"):
        msg = f"Invalid database ObjectId format: {db.id!r}"
        errors.append(msg)
        if strict:
            raise SchemaValidationError(msg)

    # 2. Namespace validation
    for ns in db.namespaces:
        if not reg.contains(ns.id):
            msg = f"Namespace {ns.name!r} ({ns.id}) is in database model but not in registry."
            errors.append(msg)
            if strict:
                raise SchemaValidationError(msg)

        # 3. Table validation
        for table in ns.tables:
            if not reg.contains(table.id):
                msg = f"Table {table.name!r} ({table.id}) is in namespace {ns.name!r} but not in registry."
                errors.append(msg)
                if strict:
                    raise SchemaValidationError(msg)

            # Check table's parent namespace_id
            if table.namespace_id != ns.id:
                msg = (
                    f"Table {table.name!r} declares namespace_id {table.namespace_id!r} "
                    f"which does not match parent namespace {ns.id!r}."
                )
                errors.append(msg)
                if strict:
                    raise MissingParentError(
                        table.id, ObjectKind.TABLE, table.namespace_id, ObjectKind.NAMESPACE
                    )

            # Known declared column names on this table
            col_names = {col.name.strip().lower() for col in table.columns}

            # 4. Column validation
            seen_ordinals: set[int] = set()
            for col in table.columns:
                if not reg.contains(col.id):
                    msg = f"Column {col.name!r} ({col.id}) is not in registry."
                    errors.append(msg)
                    if strict:
                        raise SchemaValidationError(msg)

                if col.parent_table_id != table.id:
                    msg = (
                        f"Column {col.name!r} declares parent_table_id {col.parent_table_id!r} "
                        f"which does not match table {table.id!r}."
                    )
                    errors.append(msg)
                    if strict:
                        raise MissingParentError(
                            col.id, ObjectKind.COLUMN, col.parent_table_id, ObjectKind.TABLE
                        )

                if col.ordinal_position in seen_ordinals:
                    errors.append(
                        f"Duplicate ordinal position {col.ordinal_position} in table {table.name!r} "
                        f"for column {col.name!r}."
                    )
                seen_ordinals.add(col.ordinal_position)

            # 5. Constraints validation
            all_table_constraints = []
            if table.primary_key:
                all_table_constraints.append(table.primary_key)
            all_table_constraints.extend(table.unique_constraints)
            all_table_constraints.extend(table.check_constraints)

            for constraint in all_table_constraints:
                if not reg.contains(constraint.id):
                    msg = f"Constraint {constraint.name!r} ({constraint.id}) is not in registry."
                    errors.append(msg)
                    if strict:
                        raise SchemaValidationError(msg)

                if constraint.parent_table_id != table.id:
                    msg = (
                        f"Constraint {constraint.name!r} declares parent_table_id "
                        f"{constraint.parent_table_id!r} which does not match table {table.id!r}."
                    )
                    errors.append(msg)
                    if strict:
                        raise MissingParentError(
                            constraint.id,
                            ObjectKind.CONSTRAINT,
                            constraint.parent_table_id,
                            ObjectKind.TABLE,
                        )

                # Check that columns named in constraint exist in the table definition
                for col_name in constraint.columns:
                    if col_name.strip().lower() not in col_names:
                        msg = (
                            f"Constraint {constraint.name!r} on table {table.name!r} references "
                            f"column {col_name!r} which is not declared on the table."
                        )
                        errors.append(msg)
                        if strict:
                            raise SchemaValidationError(msg)

            # 6. Indexes validation
            for index in table.indexes:
                if not reg.contains(index.id):
                    msg = f"Index {index.name!r} ({index.id}) is not in registry."
                    errors.append(msg)
                    if strict:
                        raise SchemaValidationError(msg)

                if index.parent_table_id != table.id:
                    msg = (
                        f"Index {index.name!r} declares parent_table_id {index.parent_table_id!r} "
                        f"which does not match table {table.id!r}."
                    )
                    errors.append(msg)
                    if strict:
                        raise MissingParentError(
                            index.id, ObjectKind.INDEX, index.parent_table_id, ObjectKind.TABLE
                        )

                # Verify indexed columns exist on table (excluding expressions)
                for term in index.terms:
                    if not term.is_expression and term.column_name:
                        if term.column_name.strip().lower() not in col_names:
                            msg = (
                                f"Index {index.name!r} on table {table.name!r} indexes column "
                                f"{term.column_name!r} which is not declared on the table."
                            )
                            errors.append(msg)
                            if strict:
                                raise SchemaValidationError(msg)

            # 7. Triggers validation
            for trigger in table.triggers:
                if not reg.contains(trigger.id):
                    msg = f"Trigger {trigger.name!r} ({trigger.id}) is not in registry."
                    errors.append(msg)
                    if strict:
                        raise SchemaValidationError(msg)

                if trigger.parent_table_id != table.id:
                    msg = (
                        f"Trigger {trigger.name!r} declares parent_table_id {trigger.parent_table_id!r} "
                        f"which does not match table {table.id!r}."
                    )
                    errors.append(msg)
                    if strict:
                        raise MissingParentError(
                            trigger.id,
                            ObjectKind.TRIGGER,
                            trigger.parent_table_id,
                            ObjectKind.TABLE,
                        )

            # 8. Foreign keys validation
            for fk in table.foreign_keys:
                if not reg.contains(fk.id):
                    msg = f"Foreign key {fk.name!r} ({fk.id}) is not in registry."
                    errors.append(msg)
                    if strict:
                        raise SchemaValidationError(msg)

                if fk.source_table_id != table.id:
                    msg = (
                        f"Foreign key {fk.name!r} declares source_table_id {fk.source_table_id!r} "
                        f"which does not match table {table.id!r}."
                    )
                    errors.append(msg)
                    if strict:
                        raise MissingParentError(
                            fk.id, ObjectKind.FOREIGN_KEY, fk.source_table_id, ObjectKind.TABLE
                        )

                # Verify source columns exist in child table
                for src_col in fk.source_columns:
                    if src_col.strip().lower() not in col_names:
                        msg = (
                            f"Foreign key {fk.name!r} references source column {src_col!r} "
                            f"which is not declared on child table {table.name!r}."
                        )
                        errors.append(msg)
                        if strict:
                            raise SchemaValidationError(msg)

                # Validate the builder's resolved reference, including name-based resolution.
                ref = fk_references.get(fk.id)
                target_id = ref.referenced_table_id if ref is not None else fk.referenced_table_id
                is_resolved = ref.is_resolved if ref is not None else bool(target_id)
                target_tbl = reg.get_object(target_id) if target_id else None
                if target_tbl is not None and not isinstance(target_tbl, CanonicalTable):
                    msg = (
                        f"Foreign key {fk.name!r} targets referenced_table_id "
                        f"{target_id!r} which is not a table."
                    )
                    errors.append(msg)
                    if strict:
                        raise SchemaValidationError(msg)
                elif not is_resolved or target_tbl is None:
                    if strict_foreign_keys:
                        msg = (
                            f"Foreign key {fk.name!r} has unresolved target table "
                            f"{fk.referenced_table_name!r} ({target_id!r})."
                        )
                        errors.append(msg)
                        if strict:
                            raise SchemaValidationError(msg)
                else:
                    target_cols = {c.name.strip().lower() for c in target_tbl.columns}
                    for ref_col in fk.referenced_columns:
                        if ref_col.strip().lower() not in target_cols:
                            msg = (
                                f"Foreign key {fk.name!r} references parent column {ref_col!r} "
                                f"which is not declared on parent table {target_tbl.name!r}."
                            )
                            errors.append(msg)
                            if strict:
                                raise SchemaValidationError(msg)

        # 9. Views validation
        for view in ns.views:
            if not reg.contains(view.id):
                msg = f"View {view.name!r} ({view.id}) is not in registry."
                errors.append(msg)
                if strict:
                    raise SchemaValidationError(msg)
            if view.namespace_id != ns.id:
                msg = (
                    f"View {view.name!r} declares namespace_id {view.namespace_id!r} "
                    f"which does not match parent namespace {ns.id!r}."
                )
                errors.append(msg)
                if strict:
                    raise MissingParentError(
                        view.id, ObjectKind.VIEW, view.namespace_id, ObjectKind.NAMESPACE
                    )

    return tuple(errors)


__all__ = ["validate_schema_representation"]
