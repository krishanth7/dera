"""DERA Canonical Metadata Normalization & Identity — Validation & Integrity.

Validates reference integrity, detects identity collisions, and enforces resource
security limits on canonical schema snapshots.
"""

from __future__ import annotations

from dera.metadata.errors import (
    DuplicateIdentityError,
    InvalidReferenceError,
    MetadataLimitExceededError,
)
from dera.metadata.models.database import CanonicalDatabase

MAX_IDENTIFIER_LENGTH: int = 1024
MAX_DEFINITION_LENGTH: int = 1_048_576  # 1 MB
MAX_TOTAL_OBJECTS: int = 100_000


def validate_identifier_length(name: str, context: str = "identifier") -> None:
    """Ensure identifier does not exceed safe length boundary."""
    if len(name) > MAX_IDENTIFIER_LENGTH:
        raise MetadataLimitExceededError(
            f"{context} exceeds maximum length {MAX_IDENTIFIER_LENGTH}: '{name[:32]}...'"
        )


def validate_definition_length(defn: str | None, context: str = "definition") -> None:
    """Ensure raw SQL definition does not exceed 1 MB."""
    if defn and len(defn.encode("utf-8")) > MAX_DEFINITION_LENGTH:
        raise MetadataLimitExceededError(
            f"{context} exceeds maximum size {MAX_DEFINITION_LENGTH} bytes."
        )


def validate_canonical_database(database: CanonicalDatabase) -> None:
    """Perform comprehensive reference integrity, uniqueness, and bounds checks."""
    seen_ids: dict[str, str] = {}
    table_lookup: set[str] = set()
    total_objects = 1

    # 1. Register Database ID
    seen_ids[database.id] = f"Database({database.name})"

    # 2. Iterate Namespaces
    for ns in database.namespaces:
        total_objects += 1
        validate_identifier_length(ns.name, "Namespace name")
        if ns.id in seen_ids:
            raise DuplicateIdentityError(
                f"Duplicate identity detected for namespace '{ns.name}' (id={ns.id}). "
                f"Collides with {seen_ids[ns.id]}."
            )
        seen_ids[ns.id] = f"Namespace({ns.name})"

        # 3. Iterate Tables
        for tbl in ns.tables:
            total_objects += 1
            validate_identifier_length(tbl.name, "Table name")
            if tbl.id in seen_ids:
                raise DuplicateIdentityError(
                    f"Duplicate identity detected for table '{tbl.name}' (id={tbl.id}). "
                    f"Collides with {seen_ids[tbl.id]}."
                )
            seen_ids[tbl.id] = f"Table({ns.name}.{tbl.name})"
            table_lookup.add(tbl.id)

            col_names: set[str] = set()

            # Columns
            for col in tbl.columns:
                total_objects += 1
                validate_identifier_length(col.name, f"Column name in {tbl.name}")
                if col.id in seen_ids:
                    raise DuplicateIdentityError(
                        f"Duplicate identity detected for column '{tbl.name}.{col.name}' (id={col.id}). "
                        f"Collides with {seen_ids[col.id]}."
                    )
                seen_ids[col.id] = f"Column({tbl.name}.{col.name})"
                col_names.add(col.name.lower())

            # Constraints
            for c in tbl.unique_constraints + tbl.check_constraints:
                total_objects += 1
                if c.id in seen_ids:
                    raise DuplicateIdentityError(
                        f"Duplicate identity detected for constraint '{c.name}' on {tbl.name} (id={c.id}). "
                        f"Collides with {seen_ids[c.id]}."
                    )
                seen_ids[c.id] = f"Constraint({tbl.name}.{c.name})"

            if tbl.primary_key:
                total_objects += 1
                pk = tbl.primary_key
                if pk.id in seen_ids:
                    raise DuplicateIdentityError(
                        f"Duplicate identity detected for PK '{pk.name}' on {tbl.name} (id={pk.id}). "
                        f"Collides with {seen_ids[pk.id]}."
                    )
                seen_ids[pk.id] = f"PrimaryKey({tbl.name}.{pk.name})"
                # Verify PK columns exist in table
                for pk_col in pk.columns:
                    if pk_col.lower() not in col_names:
                        raise InvalidReferenceError(
                            f"Primary key '{pk.name}' references non-existent column '{pk_col}' in table '{tbl.name}'."
                        )

            # Foreign Keys
            for fk in tbl.foreign_keys:
                total_objects += 1
                if fk.id in seen_ids:
                    raise DuplicateIdentityError(
                        f"Duplicate identity detected for foreign key '{fk.name}' on {tbl.name} (id={fk.id}). "
                        f"Collides with {seen_ids[fk.id]}."
                    )
                seen_ids[fk.id] = f"ForeignKey({tbl.name}.{fk.name})"
                for src_col in fk.source_columns:
                    if src_col.lower() not in col_names:
                        raise InvalidReferenceError(
                            f"Foreign key '{fk.name}' references non-existent source column '{src_col}' in table '{tbl.name}'."
                        )

            # Indexes
            for idx in tbl.indexes:
                total_objects += 1
                if idx.id in seen_ids:
                    raise DuplicateIdentityError(
                        f"Duplicate identity detected for index '{idx.name}' on {tbl.name} (id={idx.id}). "
                        f"Collides with {seen_ids[idx.id]}."
                    )
                seen_ids[idx.id] = f"Index({tbl.name}.{idx.name})"
                for term in idx.terms:
                    if not term.is_expression and term.column_name:
                        if term.column_name.lower() not in col_names:
                            raise InvalidReferenceError(
                                f"Index '{idx.name}' references non-existent column '{term.column_name}' in table '{tbl.name}'."
                            )

            # Triggers
            for tr in tbl.triggers:
                total_objects += 1
                validate_definition_length(tr.definition, f"Trigger definition '{tr.name}'")
                if tr.id in seen_ids:
                    raise DuplicateIdentityError(
                        f"Duplicate identity detected for trigger '{tr.name}' on {tbl.name} (id={tr.id}). "
                        f"Collides with {seen_ids[tr.id]}."
                    )
                seen_ids[tr.id] = f"Trigger({tbl.name}.{tr.name})"

        # Views
        for v in ns.views:
            total_objects += 1
            validate_identifier_length(v.name, "View name")
            validate_definition_length(v.definition, f"View definition '{v.name}'")
            if v.id in seen_ids:
                raise DuplicateIdentityError(
                    f"Duplicate identity detected for view '{v.name}' in {ns.name} (id={v.id}). "
                    f"Collides with {seen_ids[v.id]}."
                )
            seen_ids[v.id] = f"View({ns.name}.{v.name})"

    # Check overall object count limit
    if total_objects > MAX_TOTAL_OBJECTS:
        raise MetadataLimitExceededError(
            f"Total schema objects ({total_objects}) exceeds maximum limit ({MAX_TOTAL_OBJECTS})."
        )
