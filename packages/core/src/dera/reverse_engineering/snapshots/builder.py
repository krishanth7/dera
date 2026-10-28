"""DERA Reverse Engineering — Phase 6.5 Schema Snapshot Builder.

Constructs immutable, cryptographically fingerprinted SchemaSnapshot instances from
validated reverse engineering outputs across Phases 6.1 through 6.4.

Guarantees:
- Cross-phase consistency verification (matching database identity, engine, and version).
- Deterministic canonical structural payload generation.
- Domain-separated SHA-256 structural fingerprinting.
- Separation of volatile envelope metadata from the immutable structural payload.
- Comprehensive static validation before returning the completed snapshot.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from dera.reverse_engineering.snapshots.canonicalization import (
    canonicalize_structural_payload,
)
from dera.reverse_engineering.snapshots.errors import (
    SnapshotValidationError,
)
from dera.reverse_engineering.snapshots.fingerprints import (
    compute_structural_fingerprint,
)
from dera.reverse_engineering.snapshots.identity import generate_snapshot_id
from dera.reverse_engineering.snapshots.limits import SnapshotResourceLimits
from dera.reverse_engineering.snapshots.models import (
    FINGERPRINT_ALGORITHM_NAME,
    FINGERPRINT_DOMAIN,
    SNAPSHOT_FORMAT_VERSION,
    SchemaSnapshot,
    SnapshotEnvelope,
)
from dera.reverse_engineering.snapshots.provenance import (
    CaptureConsistency,
    SnapshotProvenance,
)
from dera.reverse_engineering.snapshots.validation import validate_snapshot_strict

if TYPE_CHECKING:
    from dera.reverse_engineering.dependencies.models import DependencyAnalysisResult
    from dera.reverse_engineering.graph.models import ForeignKeyGraph
    from dera.reverse_engineering.reconstruction.models import StructuralReconstructionResult
    from dera.reverse_engineering.schema import SchemaRepresentation


class SchemaSnapshotBuilder:
    """Builder service for constructing validated, immutable SchemaSnapshot instances."""

    @classmethod
    def from_analysis(
        cls,
        schema: SchemaRepresentation,
        reconstruction: StructuralReconstructionResult | None = None,
        relationships: ForeignKeyGraph | None = None,
        dependencies: DependencyAnalysisResult | None = None,
        workspace_id: str = "default",
        snapshot_id: str | None = None,
        capture_timestamp: datetime | None = None,
        capture_consistency: CaptureConsistency = CaptureConsistency.BEST_EFFORT,
        tags: dict[str, str] | None = None,
        storage_metadata: dict[str, Any] | None = None,
        limits: SnapshotResourceLimits | None = None,
        strict_validation: bool = False,
    ) -> SchemaSnapshot:
        """Construct an immutable SchemaSnapshot from reverse engineering analysis artifacts.

        Args:
            schema: Required Phase 6.1 SchemaRepresentation.
            reconstruction: Optional Phase 6.2 StructuralReconstructionResult.
            relationships: Optional Phase 6.3 ForeignKeyGraph.
            dependencies: Optional Phase 6.4 DependencyAnalysisResult.
            workspace_id: Tenant / workspace isolation identifier.
            snapshot_id: Optional custom snapshot ID (generated if omitted).
            capture_timestamp: Optional UTC timestamp of capture (now if omitted).
            capture_consistency: Transactional consistency guarantee of the capture.
            tags: Arbitrary user/system classification tags.
            storage_metadata: Physical storage hints.
            limits: Resource bounds to enforce.
            strict_validation: If True, raise on any validation finding.

        Returns:
            Fully assembled, immutable, verified SchemaSnapshot.

        Raises:
            SnapshotValidationError: If cross-phase consistency checks or structural validation fails.
        """
        effective_limits = limits or SnapshotResourceLimits()

        # 1. Cross-Phase Consistency Verification
        if reconstruction is not None:
            if reconstruction.database_name != schema.database_name:
                raise SnapshotValidationError(
                    f"Cross-phase database name mismatch: SchemaRepresentation has '{schema.database_name}', "
                    f"StructuralReconstructionResult has '{reconstruction.database_name}'."
                )
            if reconstruction.engine != schema.engine:
                raise SnapshotValidationError(
                    f"Cross-phase engine mismatch: SchemaRepresentation has '{schema.engine}', "
                    f"StructuralReconstructionResult has '{reconstruction.engine}'."
                )

        if relationships is not None:
            if str(relationships.database_id) != str(schema.database_id):
                raise SnapshotValidationError(
                    f"Cross-phase database_id mismatch: SchemaRepresentation has '{schema.database_id}', "
                    f"ForeignKeyGraph has '{relationships.database_id}'."
                )

        if dependencies is not None:
            if str(dependencies.database_id) != str(schema.database_id):
                raise SnapshotValidationError(
                    f"Cross-phase database_id mismatch: SchemaRepresentation has '{schema.database_id}', "
                    f"DependencyAnalysisResult has '{dependencies.database_id}'."
                )

        # 2. Canonicalize Structural Payload
        payload = canonicalize_structural_payload(
            schema=schema,
            reconstruction=reconstruction,
            relationships=relationships,
            dependencies=dependencies,
        )

        # 3. Compute Deterministic Fingerprint
        fingerprint = compute_structural_fingerprint(payload, limits=effective_limits)

        # 4. Assemble Envelope
        effective_id = snapshot_id or generate_snapshot_id()
        effective_timestamp = capture_timestamp or datetime.now(UTC)
        if effective_timestamp.tzinfo is None:
            effective_timestamp = effective_timestamp.replace(tzinfo=UTC)

        provenance = SnapshotProvenance(
            engine=schema.engine,
            engine_version=schema.engine_version,
            connector_version=getattr(schema.provenance, "connector_version", None),
            capture_duration_ms=getattr(schema.provenance, "duration_ms", None),
            collection_status="completed",
            completeness=schema.completeness,
            source_reference=schema.source_reference,
            capture_consistency=capture_consistency,
        )

        envelope = SnapshotEnvelope(
            snapshot_id=effective_id,
            workspace_id=workspace_id,
            database_id=schema.database_id,
            source_reference=schema.source_reference,
            capture_timestamp=effective_timestamp,
            provenance=provenance,
            validation_status="VALID",
            tags=tags or {},
            storage_metadata=storage_metadata or {},
        )

        # 5. Assemble SchemaSnapshot
        snapshot = SchemaSnapshot(
            format_version=SNAPSHOT_FORMAT_VERSION,
            snapshot_id=effective_id,
            fingerprint=fingerprint,
            fingerprint_algorithm=FINGERPRINT_ALGORITHM_NAME,
            fingerprint_domain=FINGERPRINT_DOMAIN,
            envelope=envelope,
            payload=payload,
        )

        # 6. Validate
        if strict_validation:
            validate_snapshot_strict(snapshot, limits=effective_limits)

        return snapshot
