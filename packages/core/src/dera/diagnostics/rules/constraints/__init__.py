"""DERA Diagnostics: Constraint Rules."""

from __future__ import annotations

from dera.diagnostics.protocols import DiagnosticRule
from dera.diagnostics.rules.constraints.check_constraints import CheckConstraintMetadataRule
from dera.diagnostics.rules.constraints.constraint_integrity import ConstraintColumnIntegrityRule
from dera.diagnostics.rules.constraints.foreign_keys import ForeignKeyIntegrityRule
from dera.diagnostics.rules.constraints.primary_keys import PrimaryKeyIntegrityRule
from dera.diagnostics.rules.constraints.unique_constraints import UniqueConstraintIntegrityRule

ALL_CONSTRAINT_RULES: list[DiagnosticRule] = [
    PrimaryKeyIntegrityRule(),
    ForeignKeyIntegrityRule(),
    UniqueConstraintIntegrityRule(),
    CheckConstraintMetadataRule(),
    ConstraintColumnIntegrityRule(),
]

__all__ = [
    "PrimaryKeyIntegrityRule",
    "ForeignKeyIntegrityRule",
    "UniqueConstraintIntegrityRule",
    "CheckConstraintMetadataRule",
    "ConstraintColumnIntegrityRule",
    "ALL_CONSTRAINT_RULES",
]
