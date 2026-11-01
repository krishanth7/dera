"""DERA Diagnostics — Finding Ordering Engine.

Applies stable, multi-factor deterministic sorting to diagnostic findings,
eliminating non-deterministic jitter across diagnostic evaluations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    pass


def get_finding_sort_key(finding: Any) -> tuple[int, int, int, str, str, str]:
    """Generates a stable 6-element sort key for diagnostic findings.

    Sort order:
      1. Effective severity rank (DESC -> negated)
      2. Finding confidence rank (DESC -> negated)
      3. Classification priority weight (DESC -> negated)
      4. Canonical object identity (ASC)
      5. Rule ID (ASC)
      6. Finding fingerprint (ASC)
    """
    sev_rank = getattr(finding.severity, "rank", 1)

    # Handle confidence if present, else fallback
    confidence = getattr(finding, "confidence", None)
    conf_rank = getattr(confidence, "rank", 4) if confidence else 4

    # Handle classification if present, else fallback
    classification = getattr(finding, "classification", None)
    class_weight = getattr(classification, "priority_weight", 50) if classification else 50

    return (
        -sev_rank,
        -conf_rank,
        -class_weight,
        str(finding.object_id),
        str(finding.rule_id),
        str(finding.fingerprint),
    )


def sort_findings_deterministically(findings: list[Any]) -> list[Any]:
    """Sorts a list of findings using the canonical 6-element deterministic sort key."""
    return sorted(findings, key=get_finding_sort_key)
