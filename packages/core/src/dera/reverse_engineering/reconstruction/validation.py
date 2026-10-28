"""Structural validation engine for Phase 6.2 Structural Reconstruction.

Performs comprehensive validation of reconstructed tables, columns, primary keys,
foreign keys, unique constraints, and check constraints, emitting structured findings
with Error, Warning, and Informational severity levels.
"""

from collections.abc import Sequence

from dera.metadata.enums import MetadataCompleteness
from dera.metadata.identity import ObjectId
from dera.reverse_engineering.reconstruction.errors import StructuralValidationError
from dera.reverse_engineering.reconstruction.models import (
    ReconstructedTable,
    ReconstructionMode,
    StructuralValidationFinding,
    ValidationSeverity,
)
from dera.reverse_engineering.references import ResolutionStatus


def validate_structural_reconstruction(
    tables: Sequence[ReconstructedTable],
    mode: ReconstructionMode = ReconstructionMode.STRICT,
) -> tuple[StructuralValidationFinding, ...]:
    """Validate the reconstructed tables and constraints.

    In STRICT mode, raises StructuralValidationError if any finding has ERROR severity.
    In PARTIAL mode, preserves findings for downstream inspection without raising.
    """
    findings: list[StructuralValidationFinding] = []

    seen_table_identities: set[ObjectId] = set()
    seen_table_names: set[tuple[str, str]] = set()
    seen_constraint_identities: set[ObjectId] = set()
    table_map: dict[ObjectId, ReconstructedTable] = {}
    table_name_map: dict[tuple[str, str], ReconstructedTable] = {}

    for tbl in tables:
        # Check duplicate table ObjectId
        if tbl.object_id in seen_table_identities:
            findings.append(
                StructuralValidationFinding(
                    severity=ValidationSeverity.ERROR,
                    code="DUPLICATE_TABLE_ID",
                    message=f"Duplicate table ObjectId '{tbl.object_id}' detected.",
                    object_id=tbl.object_id,
                )
            )
        seen_table_identities.add(tbl.object_id)

        # Check duplicate (namespace, name)
        name_key = (tbl.namespace, tbl.native_name)
        if name_key in seen_table_names:
            findings.append(
                StructuralValidationFinding(
                    severity=ValidationSeverity.ERROR,
                    code="DUPLICATE_TABLE_NAME",
                    message=f"Duplicate table name '{tbl.native_name}' in namespace '{tbl.namespace}'.",
                    object_id=tbl.object_id,
                )
            )
        seen_table_names.add(name_key)
        table_map[tbl.object_id] = tbl
        table_name_map[name_key] = tbl

    for tbl in tables:
        # 1. Column Validations
        seen_col_names: set[str] = set()
        seen_ordinals: set[int] = set()

        for col in tbl.columns:
            if col.native_name in seen_col_names:
                findings.append(
                    StructuralValidationFinding(
                        severity=ValidationSeverity.ERROR,
                        code="DUPLICATE_COLUMN_NAME",
                        message=f"Table '{tbl.native_name}' has duplicate column '{col.native_name}'.",
                        object_id=col.object_id,
                    )
                )
            seen_col_names.add(col.native_name)

            if col.ordinal_position in seen_ordinals:
                findings.append(
                    StructuralValidationFinding(
                        severity=ValidationSeverity.WARNING,
                        code="DUPLICATE_ORDINAL_POSITION",
                        message=f"Table '{tbl.native_name}' has duplicate ordinal position {col.ordinal_position}.",
                        object_id=col.object_id,
                    )
                )
            seen_ordinals.add(col.ordinal_position)

        # 2. Primary Key Validations
        if tbl.primary_key:
            pk = tbl.primary_key
            if pk.object_id in seen_constraint_identities:
                findings.append(
                    StructuralValidationFinding(
                        severity=ValidationSeverity.ERROR,
                        code="DUPLICATE_CONSTRAINT_ID",
                        message=f"Duplicate constraint ObjectId '{pk.object_id}'.",
                        object_id=pk.object_id,
                    )
                )
            seen_constraint_identities.add(pk.object_id)

            for col_name in pk.column_names:
                if col_name not in seen_col_names:
                    findings.append(
                        StructuralValidationFinding(
                            severity=ValidationSeverity.ERROR,
                            code="INVALID_PRIMARY_KEY_COLUMN",
                            message=f"Primary key column '{col_name}' does not exist on table '{tbl.native_name}'.",
                            object_id=pk.object_id,
                        )
                    )

        # 3. Unique Constraint Validations
        for u in tbl.unique_constraints:
            if u.object_id in seen_constraint_identities:
                findings.append(
                    StructuralValidationFinding(
                        severity=ValidationSeverity.ERROR,
                        code="DUPLICATE_CONSTRAINT_ID",
                        message=f"Duplicate unique constraint ObjectId '{u.object_id}'.",
                        object_id=u.object_id,
                    )
                )
            seen_constraint_identities.add(u.object_id)

            for col_name in u.column_names:
                if col_name not in seen_col_names:
                    findings.append(
                        StructuralValidationFinding(
                            severity=ValidationSeverity.ERROR,
                            code="INVALID_UNIQUE_COLUMN",
                            message=f"Unique constraint '{u.native_name or u.object_id}' column '{col_name}' not in table '{tbl.native_name}'.",
                            object_id=u.object_id,
                        )
                    )

        # 4. Check Constraint Validations
        for ck in tbl.check_constraints:
            if ck.object_id in seen_constraint_identities:
                findings.append(
                    StructuralValidationFinding(
                        severity=ValidationSeverity.ERROR,
                        code="DUPLICATE_CONSTRAINT_ID",
                        message=f"Duplicate check constraint ObjectId '{ck.object_id}'.",
                        object_id=ck.object_id,
                    )
                )
            seen_constraint_identities.add(ck.object_id)

            if not ck.expression or not ck.expression.strip():
                findings.append(
                    StructuralValidationFinding(
                        severity=ValidationSeverity.ERROR,
                        code="EMPTY_CHECK_EXPRESSION",
                        message=f"Check constraint '{ck.native_name or ck.object_id}' has an empty expression.",
                        object_id=ck.object_id,
                    )
                )

        # 5. Foreign Key Validations
        for fk in tbl.foreign_keys:
            if fk.object_id in seen_constraint_identities:
                findings.append(
                    StructuralValidationFinding(
                        severity=ValidationSeverity.ERROR,
                        code="DUPLICATE_CONSTRAINT_ID",
                        message=f"Duplicate foreign key ObjectId '{fk.object_id}'.",
                        object_id=fk.object_id,
                    )
                )
            seen_constraint_identities.add(fk.object_id)

            # Check column count equality
            if fk.referenced_column_names and len(fk.source_column_names) != len(
                fk.referenced_column_names
            ):
                findings.append(
                    StructuralValidationFinding(
                        severity=ValidationSeverity.ERROR,
                        code="FOREIGN_KEY_COLUMN_COUNT_MISMATCH",
                        message=f"Foreign key '{fk.native_name or fk.object_id}' has {len(fk.source_column_names)} source columns but {len(fk.referenced_column_names)} referenced columns.",
                        object_id=fk.object_id,
                    )
                )

            # Source column existence
            for sc in fk.source_column_names:
                if sc not in seen_col_names:
                    findings.append(
                        StructuralValidationFinding(
                            severity=ValidationSeverity.ERROR,
                            code="INVALID_FOREIGN_KEY_SOURCE_COLUMN",
                            message=f"Foreign key '{fk.native_name or fk.object_id}' source column '{sc}' not in table '{tbl.native_name}'.",
                            object_id=fk.object_id,
                        )
                    )

            # Target resolution status
            if fk.resolution_status in (ResolutionStatus.MISSING, ResolutionStatus.INVALID):
                is_partial = tbl.completeness in (
                    MetadataCompleteness.PARTIAL,
                    MetadataCompleteness.RESTRICTED,
                )
                severity = (
                    ValidationSeverity.WARNING
                    if is_partial or mode == ReconstructionMode.PARTIAL
                    else ValidationSeverity.ERROR
                )
                code = (
                    "MISSING_FOREIGN_KEY_TARGET"
                    if fk.resolution_status == ResolutionStatus.MISSING
                    else "INVALID_FOREIGN_KEY_TARGET"
                )
                findings.append(
                    StructuralValidationFinding(
                        severity=severity,
                        code=code,
                        message=f"Foreign key '{fk.native_name or fk.object_id}' references missing or invalid target '{fk.referenced_table_name}'.",
                        object_id=fk.object_id,
                        details={
                            "referenced_table": fk.referenced_table_name,
                            "referenced_namespace": fk.referenced_namespace,
                            "status": fk.resolution_status.value,
                        },
                    )
                )

    # Deterministic sorting of findings with hierarchical entity priority
    code_priority = {
        "DUPLICATE_TABLE_ID": 0,
        "DUPLICATE_TABLE_NAME": 1,
        "DUPLICATE_COLUMN_NAME": 2,
        "DUPLICATE_ORDINAL_POSITION": 3,
        "DUPLICATE_CONSTRAINT_ID": 4,
        "DUPLICATE_CONSTRAINT_NAME": 5,
        "INVALID_PRIMARY_KEY": 6,
        "INVALID_FOREIGN_KEY_SOURCE": 7,
        "INVALID_FOREIGN_KEY_TARGET": 8,
        "MISSING_FOREIGN_KEY_TARGET": 9,
    }
    findings.sort(
        key=lambda f: (
            f.severity.value,
            code_priority.get(f.code, 99),
            f.code,
            str(f.object_id or ""),
            f.message,
        )
    )

    # Strict mode enforcement
    if mode == ReconstructionMode.STRICT:
        errors = [f for f in findings if f.severity == ValidationSeverity.ERROR]
        if errors:
            err_msg = "; ".join(e.message for e in errors[:5])
            if len(errors) > 5:
                err_msg += f" (and {len(errors) - 5} more)"
            raise StructuralValidationError(
                f"Strict structural validation failed with {len(errors)} error(s): {err_msg}",
                details={"errors": [e.model_dump() for e in errors]},
            )

    return tuple(findings)
