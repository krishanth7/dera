"""DERA Comparison — Phase 9.1 Compatibility Validation.

Implements strict validation of snapshot format versions, database engines,
and required metadata before schema diff evaluation begins.
"""

from __future__ import annotations

from dataclasses import dataclass

from dera.comparison.errors import (
    IncompatibleSnapshotError,
    InvalidSnapshotError,
    UnsupportedEngineComparisonError,
)
from dera.reverse_engineering.snapshots.compatibility import (
    SUPPORTED_SNAPSHOT_FORMAT_VERSIONS,
)
from dera.reverse_engineering.snapshots.models import SchemaSnapshot

SUPPORTED_ENGINES: frozenset[str] = frozenset(
    [
        "postgresql",
        "supabase",
        "sqlite",
        "mysql",
        "mariadb",
    ]
)

# Canonical engine equivalence classes where cross-comparison is proven safe
ENGINE_EQUIVALENCE_CLASSES: dict[str, str] = {
    "postgresql": "postgres_family",
    "supabase": "postgres_family",
    "mysql": "mysql_family",
    "mariadb": "mysql_family",
    "sqlite": "sqlite_family",
}


@dataclass(frozen=True)
class CompatibilityValidationResult:
    """Outcome of snapshot compatibility check."""

    is_compatible: bool
    baseline_engine: str
    target_engine: str
    is_cross_engine: bool
    notes: tuple[str, ...] = ()


class SnapshotCompatibilityValidator:
    """Validates structural snapshot compatibility for comparison."""

    @classmethod
    def validate(
        cls,
        baseline: SchemaSnapshot,
        target: SchemaSnapshot,
        allow_compatible_engine_families: bool = True,
    ) -> CompatibilityValidationResult:
        """Validate format versions and engine compatibility between two snapshots.

        Raises:
            InvalidSnapshotError: If either snapshot structure is malformed.
            IncompatibleSnapshotError: If format versions are unsupported or mismatched.
            UnsupportedEngineComparisonError: If engines belong to incompatible families.
        """
        if not isinstance(baseline, SchemaSnapshot):
            raise InvalidSnapshotError("Baseline snapshot must be a valid SchemaSnapshot instance.")
        if not isinstance(target, SchemaSnapshot):
            raise InvalidSnapshotError("Target snapshot must be a valid SchemaSnapshot instance.")

        # 1. Format version checks
        if baseline.format_version not in SUPPORTED_SNAPSHOT_FORMAT_VERSIONS:
            raise IncompatibleSnapshotError(
                f"Unsupported baseline snapshot format version: '{baseline.format_version}'."
            )
        if target.format_version not in SUPPORTED_SNAPSHOT_FORMAT_VERSIONS:
            raise IncompatibleSnapshotError(
                f"Unsupported target snapshot format version: '{target.format_version}'."
            )

        # 2. Engine validation
        b_engine = baseline.payload.engine.lower().strip()
        t_engine = target.payload.engine.lower().strip()

        if b_engine not in SUPPORTED_ENGINES:
            raise IncompatibleSnapshotError(f"Unsupported baseline database engine: '{b_engine}'.")
        if t_engine not in SUPPORTED_ENGINES:
            raise IncompatibleSnapshotError(f"Unsupported target database engine: '{t_engine}'.")

        notes: list[str] = []
        is_cross_engine = b_engine != t_engine

        if is_cross_engine:
            b_family = ENGINE_EQUIVALENCE_CLASSES.get(b_engine)
            t_family = ENGINE_EQUIVALENCE_CLASSES.get(t_engine)

            if not allow_compatible_engine_families or b_family != t_family:
                raise UnsupportedEngineComparisonError(
                    baseline_engine=b_engine,
                    target_engine=t_engine,
                )
            notes.append(
                f"Cross-engine comparison permitted within compatible family '{b_family}' "
                f"({b_engine} -> {t_engine})."
            )

        return CompatibilityValidationResult(
            is_compatible=True,
            baseline_engine=b_engine,
            target_engine=t_engine,
            is_cross_engine=is_cross_engine,
            notes=tuple(notes),
        )
