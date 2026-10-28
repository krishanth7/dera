"""DERA Reverse Engineering — Phase 6.5 Snapshot Validation.

Performs static validation of SchemaSnapshot instances, checking contract versions,
field formats, resource limits, and internal referential integrity across structural elements.
"""

from __future__ import annotations

from dera.reverse_engineering.snapshots.compatibility import (
    SnapshotCompatibilityChecker,
)
from dera.reverse_engineering.snapshots.errors import (
    SnapshotValidationError,
)
from dera.reverse_engineering.snapshots.fingerprints import validate_fingerprint_format
from dera.reverse_engineering.snapshots.identity import validate_snapshot_id
from dera.reverse_engineering.snapshots.limits import SnapshotResourceLimits
from dera.reverse_engineering.snapshots.models import SchemaSnapshot


def validate_snapshot(
    snapshot: SchemaSnapshot,
    limits: SnapshotResourceLimits | None = None,
) -> tuple[str, ...]:
    """Validate a SchemaSnapshot instance, returning a tuple of finding messages.

    Args:
        snapshot: SchemaSnapshot to validate.
        limits: Optional resource bounds.

    Returns:
        Tuple of validation issue strings (empty if valid).
    """
    effective_limits = limits or SnapshotResourceLimits()
    findings: list[str] = []

    # 1. Format version check
    if not SnapshotCompatibilityChecker.is_version_supported(snapshot.format_version):
        findings.append(f"Unsupported format version: '{snapshot.format_version}'.")

    # 2. Identifier validation
    if not validate_snapshot_id(snapshot.snapshot_id):
        findings.append(f"Invalid snapshot_id format: '{snapshot.snapshot_id}'.")

    # 3. Workspace validation
    if not snapshot.envelope.workspace_id or not snapshot.envelope.workspace_id.strip():
        findings.append("Envelope workspace_id must be a non-empty string.")

    # 4. Fingerprint format
    if not validate_fingerprint_format(snapshot.fingerprint):
        findings.append(
            f"Invalid fingerprint format: '{snapshot.fingerprint}'. Must be 64-char lowercase hex."
        )

    # 5. Resource limits check
    total_objects = (
        len(snapshot.payload.namespaces)
        + len(snapshot.payload.tables)
        + sum(len(t.columns) for t in snapshot.payload.tables)
        + sum(len(t.foreign_keys) for t in snapshot.payload.tables)
        + sum(len(t.unique_constraints) for t in snapshot.payload.tables)
        + sum(len(t.check_constraints) for t in snapshot.payload.tables)
        + sum(len(t.indexes) for t in snapshot.payload.tables)
        + len(snapshot.payload.views)
        + len(snapshot.payload.triggers)
    )
    if total_objects > effective_limits.max_object_count:
        findings.append(
            f"Object count ({total_objects}) exceeds maximum limit of {effective_limits.max_object_count}."
        )

    # 6. Referential validation within payload
    table_col_map: dict[tuple[str, str], set[str]] = {
        (t.namespace, t.name): {c.name for c in t.columns} for t in snapshot.payload.tables
    }

    for t in snapshot.payload.tables:
        t_key = (t.namespace, t.name)
        col_names = table_col_map.get(t_key, set())

        # Check identifier length
        if len(t.name) > effective_limits.max_identifier_length:
            findings.append(
                f"Table name '{t.name}' exceeds max length {effective_limits.max_identifier_length}."
            )

        # Check column names
        for col in t.columns:
            if len(col.name) > effective_limits.max_identifier_length:
                findings.append(
                    f"Column name '{col.name}' in {t.namespace}.{t.name} exceeds max identifier length."
                )

        # Primary Key columns existence
        if t.primary_key is not None:
            for pk_col in t.primary_key.columns:
                if pk_col not in col_names:
                    findings.append(
                        f"Primary key '{t.primary_key.name}' on {t.namespace}.{t.name} references non-existent column '{pk_col}'."
                    )

        # Foreign Key column existence and target table check
        for fk in t.foreign_keys:
            for src_col in fk.source_columns:
                if src_col not in col_names:
                    findings.append(
                        f"Foreign key '{fk.name}' on {t.namespace}.{t.name} references non-existent source column '{src_col}'."
                    )

        # Unique constraint columns existence
        for uq in t.unique_constraints:
            for uq_col in uq.columns:
                if uq_col not in col_names:
                    findings.append(
                        f"Unique constraint '{uq.name}' on {t.namespace}.{t.name} references non-existent column '{uq_col}'."
                    )

        # Index columns existence
        for idx in t.indexes:
            for idx_col in idx.columns:
                # Indexed expression may not be raw column name, but simple column names should match
                if idx_col.isidentifier() and idx_col not in col_names:
                    findings.append(
                        f"Index '{idx.name}' on {t.namespace}.{t.name} references non-existent column '{idx_col}'."
                    )

    # Views check
    for v in snapshot.payload.views:
        if len(v.name) > effective_limits.max_identifier_length:
            findings.append(
                f"View name '{v.name}' exceeds max length {effective_limits.max_identifier_length}."
            )

    # Triggers check
    for tr in snapshot.payload.triggers:
        if len(tr.name) > effective_limits.max_identifier_length:
            findings.append(
                f"Trigger name '{tr.name}' exceeds max length {effective_limits.max_identifier_length}."
            )

    return tuple(findings)


def validate_snapshot_strict(
    snapshot: SchemaSnapshot,
    limits: SnapshotResourceLimits | None = None,
) -> None:
    """Validate a SchemaSnapshot and raise SnapshotValidationError if any issues exist."""
    findings = validate_snapshot(snapshot, limits=limits)
    if findings:
        raise SnapshotValidationError(
            f"Snapshot '{snapshot.snapshot_id}' failed validation with {len(findings)} issues: "
            + "; ".join(findings[:5])
        )
