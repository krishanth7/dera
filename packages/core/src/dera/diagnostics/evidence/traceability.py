"""DERA Diagnostics — Evidence Traceability Matrix.

Generates deterministic traceability matrices linking diagnostic findings to
verified canonical schema entities, attributes, and provenance records.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from dera.diagnostics.models import DiagnosticFinding


def build_evidence_traceability_matrix(
    findings: tuple[DiagnosticFinding, ...] | list[DiagnosticFinding],
) -> dict[str, Any]:
    """Produces a deterministic evidence traceability summary across all findings.

    Maps affected objects to their supporting findings, rules, evidence items,
    and metadata completeness states.
    """
    object_map: dict[str, list[dict[str, Any]]] = {}
    rule_map: dict[str, list[str]] = {}

    for finding in findings:
        obj_id = finding.object_id
        if obj_id not in object_map:
            object_map[obj_id] = []

        finding_entry = {
            "fingerprint": finding.fingerprint,
            "rule_id": finding.rule_id,
            "severity": finding.severity.value,
            "evidence_count": len(finding.evidence),
            "evidence_fields": sorted([getattr(e, "field_name", "") for e in finding.evidence]),
        }
        object_map[obj_id].append(finding_entry)

        if finding.rule_id not in rule_map:
            rule_map[finding.rule_id] = []
        if obj_id not in rule_map[finding.rule_id]:
            rule_map[finding.rule_id].append(obj_id)

    # Sort deterministically
    sorted_object_map = {
        k: sorted(v, key=lambda x: (x["rule_id"], x["fingerprint"]))
        for k, v in sorted(object_map.items())
    }
    sorted_rule_map = {k: sorted(v) for k, v in sorted(rule_map.items())}

    return {
        "total_referenced_objects": len(sorted_object_map),
        "total_active_rules": len(sorted_rule_map),
        "by_object": sorted_object_map,
        "by_rule": sorted_rule_map,
    }
