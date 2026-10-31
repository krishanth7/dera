"""DERA Diagnostics — Finding Prioritization Unit Tests.

Validates finding classification taxonomy, explainable priority scoring,
multi-factor ranking, and deterministic ordering stability under input reordering.
"""

from __future__ import annotations

import random

from dera.diagnostics.enums import DiagnosticSeverity
from dera.diagnostics.evidence import DiagnosticEvidence
from dera.diagnostics.evidence.models import FindingConfidence
from dera.diagnostics.models import DiagnosticFinding
from dera.diagnostics.prioritization import (
    FindingClassification,
    PriorityRank,
    classify_rule_finding,
    compute_priority_score,
    derive_priority_rank,
    sort_findings_deterministically,
)


def test_classify_rule_finding_taxonomy() -> None:
    """Verifies deterministic classification mapping across rule categories."""
    assert (
        classify_rule_finding("DERA-CON-001") == FindingClassification.CONFIRMED_STRUCTURAL_DEFECT
    )
    assert (
        classify_rule_finding("DERA-CON-002") == FindingClassification.CONFIRMED_STRUCTURAL_DEFECT
    )
    assert classify_rule_finding("DERA-IDX-001") == FindingClassification.OPTIMIZATION_CANDIDATE
    assert classify_rule_finding("DERA-IDX-003") == FindingClassification.OPTIMIZATION_CANDIDATE
    assert (
        classify_rule_finding("DERA-DEP-001") == FindingClassification.POTENTIAL_ENGINEERING_CONCERN
    )
    assert classify_rule_finding("DERA-MNT-001") == FindingClassification.MAINTAINABILITY_CONCERN
    assert (
        classify_rule_finding("DERA-MNT-003") == FindingClassification.NAMING_CONVENTION_DEVIATION
    )


def test_priority_score_formula_and_stratification() -> None:
    """Verifies that the explainable priority score strictly stratifies by severity."""
    # Critical score range: 5000+
    score_critical = compute_priority_score(
        DiagnosticSeverity.CRITICAL,
        FindingConfidence.VERIFIED,
        FindingClassification.CONFIRMED_STRUCTURAL_DEFECT,
    )
    # High score range: 4000-4999
    score_high = compute_priority_score(
        DiagnosticSeverity.HIGH,
        FindingConfidence.VERIFIED,
        FindingClassification.CONFIRMED_STRUCTURAL_DEFECT,
    )
    # Medium score range: 3000-3999
    score_med = compute_priority_score(
        DiagnosticSeverity.MEDIUM,
        FindingConfidence.VERIFIED,
        FindingClassification.OPTIMIZATION_CANDIDATE,
    )
    # Low score range: 2000-2999
    score_low = compute_priority_score(
        DiagnosticSeverity.LOW,
        FindingConfidence.VERIFIED,
        FindingClassification.NAMING_CONVENTION_DEVIATION,
    )

    assert score_critical > score_high > score_med > score_low
    assert score_critical == (5 * 1000) + (4 * 100) + 100  # 5500
    assert score_high == (4 * 1000) + (4 * 100) + 100  # 4500


def test_derive_priority_rank() -> None:
    """Verifies PriorityRank derivation from severity."""
    assert derive_priority_rank(DiagnosticSeverity.CRITICAL) == PriorityRank.P1_CRITICAL
    assert derive_priority_rank(DiagnosticSeverity.HIGH) == PriorityRank.P2_HIGH
    assert derive_priority_rank(DiagnosticSeverity.MEDIUM) == PriorityRank.P3_MEDIUM
    assert derive_priority_rank(DiagnosticSeverity.LOW) == PriorityRank.P4_LOW
    assert derive_priority_rank(DiagnosticSeverity.INFORMATIONAL) == PriorityRank.P5_INFORMATIONAL


def test_deterministic_multi_factor_sorting() -> None:
    """Verifies that findings sort deterministically regardless of input shuffle."""
    ev = DiagnosticEvidence(object_id="public.users", field_name="pk", observed_value=None)

    f1 = DiagnosticFinding(
        rule_id="DERA-CON-001",
        rule_version="1.0.0",
        object_id="public.users",
        severity=DiagnosticSeverity.CRITICAL,
        title="Critical finding",
        description="Desc",
        evidence=(ev,),
        severity_rationale="Rationale",
    )
    f2 = DiagnosticFinding(
        rule_id="DERA-CON-002",
        rule_version="1.0.0",
        object_id="public.orders",
        severity=DiagnosticSeverity.HIGH,
        title="High finding",
        description="Desc",
        evidence=(ev,),
        severity_rationale="Rationale",
    )
    f3 = DiagnosticFinding(
        rule_id="DERA-IDX-001",
        rule_version="1.0.0",
        object_id="public.accounts",
        severity=DiagnosticSeverity.MEDIUM,
        title="Medium finding",
        description="Desc",
        evidence=(ev,),
        severity_rationale="Rationale",
    )
    f4 = DiagnosticFinding(
        rule_id="DERA-MNT-003",
        rule_version="1.0.0",
        object_id="public.audit_log",
        severity=DiagnosticSeverity.LOW,
        title="Low finding",
        description="Desc",
        evidence=(ev,),
        severity_rationale="Rationale",
    )

    expected_order = [f1, f2, f3, f4]

    # Test 10 random permutations
    items = [f1, f2, f3, f4]
    rng = random.Random(42)
    for _ in range(10):
        shuffled = list(items)
        rng.shuffle(shuffled)
        sorted_res = sort_findings_deterministically(shuffled)
        assert [f.fingerprint for f in sorted_res] == [f.fingerprint for f in expected_order]
