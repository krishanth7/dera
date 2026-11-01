"""DERA Diagnostics — Evidence Validation Engine.

Performs deterministic validation of diagnostic evidence records against
canonical schema objects, ensuring reference integrity, credential minimization,
and accurate categorical confidence assignment.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from dera.diagnostics.evidence.models import (
    EvidenceCompleteness,
    EvidenceType,
    FindingConfidence,
    TypedDiagnosticEvidence,
    sanitize_value,
)

if TYPE_CHECKING:
    from dera.diagnostics.context import DiagnosticContext


class EvidenceValidationResult:
    """Outcome of validating evidence items for a diagnostic finding."""

    def __init__(
        self,
        is_valid: bool,
        confidence: FindingConfidence,
        completeness: EvidenceCompleteness,
        validated_evidence: list[TypedDiagnosticEvidence],
        validation_messages: list[str],
    ) -> None:
        self.is_valid = is_valid
        self.confidence = confidence
        self.completeness = completeness
        self.validated_evidence = validated_evidence
        self.validation_messages = validation_messages


def _infer_evidence_type(field_name: str, observed_value: Any) -> EvidenceType:
    """Deterministically infers the EvidenceType from field names and values."""
    fn = field_name.lower()
    if "column" in fn:
        return EvidenceType.COLUMN_REFERENCE
    if "constraint" in fn or "primary_key" in fn or "foreign_key" in fn:
        return EvidenceType.CONSTRAINT_REFERENCE
    if "index" in fn:
        return EvidenceType.INDEX_REFERENCE
    if "edge" in fn or "cycle" in fn or "dependency" in fn:
        return EvidenceType.GRAPH_EDGE_REFERENCE
    if "threshold" in fn or "ratio" in fn or "count" in fn or "depth" in fn or "width" in fn:
        return EvidenceType.METRIC_OBSERVATION
    if "capability" in fn:
        return EvidenceType.METADATA_CAPABILITY_STATE
    return EvidenceType.CANONICAL_OBJECT_REFERENCE


def validate_and_enrich_evidence(
    raw_evidence: tuple[Any, ...] | list[Any],
    context: DiagnosticContext | None,
) -> EvidenceValidationResult:
    """Validates raw diagnostic evidence, sanitizes values, verifies references,
    and assigns deterministic confidence and completeness.
    """
    validated: list[TypedDiagnosticEvidence] = []
    messages: list[str] = []

    known_objects: set[str] = set()
    if context is not None:
        schema = context.schema
        if schema is None and context.snapshot is not None:
            schema = getattr(context.snapshot, "schema_representation", None)

        if schema is not None:
            for t in getattr(schema, "tables", ()):
                fqn = getattr(t, "fully_qualified_name", None)
                if fqn:
                    known_objects.add(fqn)
                name = getattr(t, "name", None)
                if name:
                    known_objects.add(name)
                obj_id = getattr(t, "object_id", None)
                if obj_id:
                    known_objects.add(obj_id)
                for c in getattr(t, "columns", ()):
                    c_name = getattr(c, "name", None)
                    if c_name:
                        if fqn:
                            known_objects.add(f"{fqn}.{c_name}")
                        if name:
                            known_objects.add(f"{name}.{c_name}")
            for v in getattr(schema, "views", ()):
                v_fqn = getattr(v, "fully_qualified_name", None)
                if v_fqn:
                    known_objects.add(v_fqn)
                v_name = getattr(v, "name", None)
                if v_name:
                    known_objects.add(v_name)
            for ns in getattr(schema, "namespaces", ()):
                ns_name = getattr(ns, "name", None)
                if ns_name:
                    known_objects.add(ns_name)

        if context.graph is not None:
            for node in getattr(context.graph, "nodes", ()):
                if isinstance(node, str):
                    known_objects.add(node)
                else:
                    node_id = getattr(node, "object_id", getattr(node, "name", None))
                    if node_id:
                        known_objects.add(str(node_id))
                    fqn = getattr(node, "fully_qualified_name", None)
                    if fqn:
                        known_objects.add(str(fqn))

    has_partial = False
    has_restricted = False
    has_unsupported = False
    has_unresolved_ref = False

    for item in raw_evidence:
        # Convert legacy or standard DiagnosticEvidence to TypedDiagnosticEvidence
        obj_id = getattr(item, "object_id", "")
        field_name = getattr(item, "field_name", "")
        observed_val = sanitize_value(getattr(item, "observed_value", None))
        expected_val = sanitize_value(getattr(item, "expected_value", None))
        msg = getattr(item, "message", "")
        provenance_ref = getattr(item, "provenance_reference", None)
        context_data = sanitize_value(getattr(item, "context_data", {}))
        ev_type = getattr(item, "evidence_type", None) or _infer_evidence_type(
            field_name, observed_val
        )

        item_completeness = getattr(item, "completeness", EvidenceCompleteness.COMPLETE)

        # Reference verification against known objects
        if known_objects and obj_id not in known_objects:
            # Check if it's a capability or synthetic object
            if not obj_id.startswith("cap_") and not obj_id.startswith("sys_"):
                has_unresolved_ref = True
                messages.append(
                    f"Evidence object_id '{obj_id}' is unresolved in canonical context."
                )

        if item_completeness == EvidenceCompleteness.PARTIAL:
            has_partial = True
        elif item_completeness == EvidenceCompleteness.RESTRICTED:
            has_restricted = True
        elif item_completeness == EvidenceCompleteness.UNSUPPORTED:
            has_unsupported = True

        typed_ev = TypedDiagnosticEvidence(
            object_id=obj_id,
            field_name=field_name,
            evidence_type=ev_type,
            observed_value=observed_val,
            expected_value=expected_val,
            completeness=item_completeness,
            message=msg,
            provenance_reference=provenance_ref,
            context_data=context_data,
        )
        validated.append(typed_ev)

    # Determine overall completeness
    if has_unsupported:
        overall_completeness = EvidenceCompleteness.UNSUPPORTED
    elif has_restricted:
        overall_completeness = EvidenceCompleteness.RESTRICTED
    elif has_partial or has_unresolved_ref:
        overall_completeness = EvidenceCompleteness.PARTIAL
    else:
        overall_completeness = EvidenceCompleteness.COMPLETE

    # Determine finding confidence
    if overall_completeness == EvidenceCompleteness.UNSUPPORTED:
        confidence = FindingConfidence.UNSUPPORTED
    elif overall_completeness in (EvidenceCompleteness.RESTRICTED, EvidenceCompleteness.PARTIAL):
        confidence = FindingConfidence.CONDITIONAL
    elif not validated:
        confidence = FindingConfidence.INCOMPLETE
    else:
        confidence = FindingConfidence.VERIFIED

    return EvidenceValidationResult(
        is_valid=True,
        confidence=confidence,
        completeness=overall_completeness,
        validated_evidence=validated,
        validation_messages=messages,
    )
