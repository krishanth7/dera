"""DERA Diagnostics — Evidence Validation and Traceability Tests.

Validates reference validation, credential minimization, completeness indicators,
categorical confidence, and traceability matrix generation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from dera.diagnostics.context import DiagnosticContext
from dera.diagnostics.enums import DiagnosticSeverity
from dera.diagnostics.evidence import (
    DiagnosticEvidence,
    EvidenceCompleteness,
    EvidenceType,
    FindingConfidence,
    TypedDiagnosticEvidence,
    build_evidence_traceability_matrix,
    create_evidence_provenance,
    sanitize_value,
    validate_and_enrich_evidence,
)
from dera.diagnostics.models import DiagnosticFinding
from dera.models import DatabaseColumn, DatabaseTable


@dataclass
class MockSchema:
    tables: list[Any] = field(default_factory=list)
    views: list[Any] = field(default_factory=list)
    namespaces: list[Any] = field(default_factory=list)


def test_credential_sanitization_in_evidence() -> None:
    """Verifies that connection strings, passwords, and tokens are redacted from evidence."""
    raw_val = "postgresql://app_user:super_secret_password@db.prod.internal:5432/main"
    sanitized = sanitize_value(raw_val)
    assert "super_secret_password" not in sanitized
    assert "://***:***@" in sanitized

    context_dict = {
        "db_password": "sensitive_password_123",
        "api_key": "sec_tok_9999",
        "nested": {
            "token": "tok_abc",
            "safe_metric": 42,
        },
    }
    sanitized_dict = sanitize_value(context_dict)
    assert sanitized_dict["db_password"] == "[REDACTED]"
    assert sanitized_dict["api_key"] == "[REDACTED]"
    assert sanitized_dict["nested"]["token"] == "[REDACTED]"
    assert sanitized_dict["nested"]["safe_metric"] == 42


def test_typed_diagnostic_evidence_validation() -> None:
    """Verifies construction and canonical dictionary representation of evidence."""
    ev = TypedDiagnosticEvidence(
        object_id="public.users",
        field_name="column_count",
        evidence_type=EvidenceType.METRIC_OBSERVATION,
        observed_value=120,
        expected_value="<= 50",
        completeness=EvidenceCompleteness.COMPLETE,
        message="Table width exceeds standard threshold",
    )
    assert ev.object_id == "public.users"
    assert ev.observed_value == 120

    canonical = ev.to_canonical_dict()
    assert canonical["evidence_type"] == "metric_observation"
    assert canonical["completeness"] == "complete"
    assert canonical["observed_value"] == 120


def test_validate_and_enrich_evidence_detects_unresolved_reference() -> None:
    """Verifies that referencing non-existent tables marks evidence as partial/unresolved."""
    col = DatabaseColumn(name="id", data_type="integer", is_nullable=False)
    table = DatabaseTable(schema="public", name="orders", columns=[col])
    schema = MockSchema(tables=[table])
    context = DiagnosticContext(schema=schema)

    raw_ev = [
        DiagnosticEvidence(
            object_id="public.missing_ghost_table",
            field_name="referenced_table",
            observed_value="does_not_exist",
        )
    ]

    res = validate_and_enrich_evidence(raw_ev, context)
    assert res.completeness == EvidenceCompleteness.PARTIAL
    assert res.confidence == FindingConfidence.CONDITIONAL
    assert any("unresolved" in msg for msg in res.validation_messages)


def test_validate_and_enrich_evidence_verified_reference() -> None:
    """Verifies that references to existing canonical tables achieve VERIFIED status."""
    col = DatabaseColumn(name="id", data_type="integer", is_nullable=False)
    table = DatabaseTable(schema="public", name="users", columns=[col])
    schema = MockSchema(tables=[table])
    context = DiagnosticContext(schema=schema)

    raw_ev = [
        DiagnosticEvidence(
            object_id="public.users",
            field_name="columns",
            observed_value=1,
            expected_value=">= 1",
        )
    ]

    res = validate_and_enrich_evidence(raw_ev, context)
    assert res.completeness == EvidenceCompleteness.COMPLETE
    assert res.confidence == FindingConfidence.VERIFIED
    assert len(res.validation_messages) == 0


def test_provenance_creation() -> None:
    """Verifies provenance metadata creation from DiagnosticContext."""
    context = DiagnosticContext(source_engine="postgresql", snapshot_id="snap_123")
    prov = create_evidence_provenance(object_id="public.users", context=context)

    assert prov.source_engine == "postgresql"
    assert prov.snapshot_id == "snap_123"
    assert prov.canonical_object_id == "public.users"
    canonical = prov.to_canonical_dict()
    assert canonical["source_engine"] == "postgresql"


def test_build_evidence_traceability_matrix() -> None:
    """Verifies generation of the evidence traceability matrix."""
    ev1 = DiagnosticEvidence(
        object_id="public.users", field_name="primary_key", observed_value=None
    )
    ev2 = DiagnosticEvidence(
        object_id="public.orders", field_name="fk_user_id", observed_value="users.id"
    )

    f1 = DiagnosticFinding(
        rule_id="DERA-CON-001",
        rule_version="1.0.0",
        object_id="public.users",
        severity=DiagnosticSeverity.HIGH,
        title="Missing PK",
        description="Users table has no PK",
        evidence=(ev1,),
        severity_rationale="Integrity baseline",
    )
    f2 = DiagnosticFinding(
        rule_id="DERA-IDX-003",
        rule_version="1.0.0",
        object_id="public.orders",
        severity=DiagnosticSeverity.MEDIUM,
        title="Unindexed FK",
        description="Orders FK is unindexed",
        evidence=(ev2,),
        severity_rationale="Performance guideline",
    )

    matrix = build_evidence_traceability_matrix([f1, f2])
    assert matrix["total_referenced_objects"] == 2
    assert matrix["total_active_rules"] == 2
    assert "public.users" in matrix["by_object"]
    assert "public.orders" in matrix["by_object"]
    assert "DERA-CON-001" in matrix["by_rule"]
    assert "DERA-IDX-003" in matrix["by_rule"]


def test_validate_and_enrich_evidence_with_unhashable_graph_nodes() -> None:
    """Verifies that graphs with node objects containing unhashable attributes (like dicts) do not raise TypeError."""
    @dataclass(frozen=True)
    class DummyGraphNode:
        object_id: str
        name: str
        fully_qualified_name: str
        native_attributes: dict[str, Any]

    @dataclass
    class DummyGraph:
        nodes: list[Any]

    node = DummyGraphNode(
        object_id="tbl_123",
        name="customers",
        fully_qualified_name="public.customers",
        native_attributes={"engine": "postgres"},
    )
    graph = DummyGraph(nodes=[node])
    context = DiagnosticContext(graph=graph)

    raw_ev = [
        DiagnosticEvidence(
            object_id="tbl_123",
            field_name="primary_key",
            observed_value=None,
        )
    ]

    res = validate_and_enrich_evidence(raw_ev, context)
    assert res.completeness == EvidenceCompleteness.COMPLETE
    assert res.confidence == FindingConfidence.VERIFIED

