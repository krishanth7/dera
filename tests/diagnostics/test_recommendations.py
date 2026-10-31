"""DERA Diagnostics — Recommendations Subsystem Unit Tests.

Validates catalog completeness, advisory safety enforcement, deterministic
parameterized templates, and non-destructive wording guarantees.
"""

from __future__ import annotations

import pytest
from dera.diagnostics.enums import DiagnosticSeverity
from dera.diagnostics.evidence import DiagnosticEvidence
from dera.diagnostics.models import DiagnosticFinding
from dera.diagnostics.recommendations import (
    RECOMMENDATION_CATALOG,
    RECOMMENDATION_CATALOG_VERSION,
    RecommendationSafetyViolationError,
    generate_structured_recommendation,
    validate_recommendation_safety,
)


def test_recommendation_catalog_version() -> None:
    """Verifies recommendation catalog version string."""
    assert RECOMMENDATION_CATALOG_VERSION == "1.0.0"


def test_recommendation_catalog_entries_integrity() -> None:
    """Verifies all entries in the recommendation catalog declare required advisory fields."""
    assert len(RECOMMENDATION_CATALOG) >= 10

    for entry in RECOMMENDATION_CATALOG:
        assert entry.recommendation_id.startswith("REC-")
        assert len(entry.applicable_rule_ids) > 0
        assert entry.title
        assert entry.description
        assert entry.suggested_action
        assert entry.risk_considerations
        assert len(entry.verification_steps) > 0
        assert entry.limitations

        # Verify no entry contains destructive SQL
        validate_recommendation_safety(entry.suggested_action)
        validate_recommendation_safety(entry.description)


def test_generate_structured_recommendation_matching() -> None:
    """Verifies structured recommendation generation matching catalog entries."""
    ev = DiagnosticEvidence(object_id="public.users", field_name="primary_key", observed_value=None)
    finding = DiagnosticFinding(
        rule_id="DERA-CON-001",
        rule_version="1.0.0",
        object_id="public.users",
        severity=DiagnosticSeverity.HIGH,
        title="Missing PK",
        description="Users table has no PK",
        evidence=(ev,),
        severity_rationale="Integrity baseline",
    )

    rec = generate_structured_recommendation(finding)
    assert rec is not None
    assert rec.recommendation_id == "REC-CON-001"
    assert rec.is_advisory is True
    assert "public.users" in rec.suggested_action
    assert rec.risk_considerations
    assert len(rec.verification_steps) > 0


def test_recommendation_safety_catches_prohibited_mutations() -> None:
    """Verifies that destructive SQL commands are rejected by the safety validator."""
    destructive_statements = [
        "DROP TABLE public.users;",
        "DROP DATABASE production;",
        "TRUNCATE TABLE logs;",
        "DELETE FROM orders WHERE 1=1;",
        "EXECUTE IMMEDIATE 'DROP TABLE t';",
    ]

    for stmt in destructive_statements:
        with pytest.raises(RecommendationSafetyViolationError):
            validate_recommendation_safety(stmt)


def test_safe_recommendation_text_passes() -> None:
    """Verifies advisory wording passes safety validation."""
    safe_texts = [
        "Evaluate whether adding an index on foreign key columns will improve query performance.",
        "Consider partitioning wide tables into separate 1-to-1 extension entities.",
        "Review circular dependency groups before planning data migration order.",
        "Adopt consistent snake_case naming across all schema identifiers.",
    ]
    for text in safe_texts:
        assert validate_recommendation_safety(text) is True
