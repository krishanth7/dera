"""Tests for all Phase 8.1 foundational diagnostic rules (DERA-SCHEMA-001 through 005)."""

from __future__ import annotations

from dataclasses import dataclass

from dera.diagnostics.context import DiagnosticContext
from dera.diagnostics.enums import (
    DiagnosticSeverity,
    EvaluationStatus,
)
from dera.diagnostics.rules.foundational import (
    CanonicalIdentityCollisionRule,
    InvalidRelationshipMappingRule,
    MissingStructuralMetadataRule,
    UnresolvedRelationshipTargetRule,
    UnsupportedCapabilityRule,
)
from dera.metadata.enums import MetadataCompleteness


# Helper mock structures to simulate SchemaRepresentation
@dataclass
class MockColumn:
    object_id: str
    name: str


@dataclass
class MockTable:
    object_id: str
    name: str
    columns: tuple[MockColumn, ...] = ()
    indexes: tuple = ()
    constraints: tuple = ()


@dataclass
class MockFKRef:
    foreign_key_id: str
    foreign_key_name: str
    source_table_name: str
    referenced_table_name: str
    source_columns: tuple[str, ...]
    referenced_columns: tuple[str, ...]
    status: str = "resolved"


@dataclass
class MockSchema:
    tables: tuple[MockTable, ...] = ()
    views: tuple = ()
    namespaces: tuple = ()
    foreign_key_references: tuple[MockFKRef, ...] = ()


@dataclass
class MockCapProfile:
    capabilities: dict[str, str]


# --- DERA-SCHEMA-001 Tests ---


def test_rule_001_unresolved_target_positive() -> None:
    rule = UnresolvedRelationshipTargetRule()
    fk = MockFKRef(
        foreign_key_id="fk_orders_user",
        foreign_key_name="fk_orders_user",
        source_table_name="orders",
        referenced_table_name="nonexistent_users",
        source_columns=("user_id",),
        referenced_columns=("id",),
        status="missing",
    )
    schema = MockSchema(foreign_key_references=(fk,))
    context = DiagnosticContext(schema=schema, completeness=MetadataCompleteness.COMPLETE)

    evaluation = rule.evaluate(context)
    assert evaluation.status == EvaluationStatus.FINDINGS_DETECTED
    assert len(evaluation.findings) == 1
    finding = evaluation.findings[0]
    assert finding.rule_id == "DERA-SCHEMA-001"
    assert finding.severity == DiagnosticSeverity.HIGH
    assert "nonexistent_users" in finding.description


def test_rule_001_unresolved_target_negative() -> None:
    rule = UnresolvedRelationshipTargetRule()
    fk = MockFKRef(
        foreign_key_id="fk_orders_user",
        foreign_key_name="fk_orders_user",
        source_table_name="orders",
        referenced_table_name="users",
        source_columns=("user_id",),
        referenced_columns=("id",),
        status="resolved",
    )
    schema = MockSchema(foreign_key_references=(fk,))
    context = DiagnosticContext(schema=schema, completeness=MetadataCompleteness.COMPLETE)

    evaluation = rule.evaluate(context)
    assert evaluation.status == EvaluationStatus.PASS
    assert len(evaluation.findings) == 0


def test_rule_001_insufficient_metadata_on_restricted() -> None:
    rule = UnresolvedRelationshipTargetRule()
    fk = MockFKRef(
        foreign_key_id="fk_orders_user",
        foreign_key_name="fk_orders_user",
        source_table_name="orders",
        referenced_table_name="remote_users",
        source_columns=("user_id",),
        referenced_columns=("id",),
        status="restricted",
    )
    schema = MockSchema(foreign_key_references=(fk,))
    context = DiagnosticContext(schema=schema, completeness=MetadataCompleteness.RESTRICTED)

    evaluation = rule.evaluate(context)
    assert evaluation.status == EvaluationStatus.INSUFFICIENT_METADATA
    assert len(evaluation.findings) == 0


# --- DERA-SCHEMA-002 Tests ---


def test_rule_002_identity_collision_positive() -> None:
    rule = CanonicalIdentityCollisionRule()
    # Two distinct tables producing the same object_id
    tbl1 = MockTable(object_id="dera:table:duplicate12345", name="table_one")
    tbl2 = MockTable(object_id="dera:table:duplicate12345", name="table_two")
    schema = MockSchema(tables=(tbl1, tbl2))
    context = DiagnosticContext(schema=schema)

    evaluation = rule.evaluate(context)
    assert evaluation.status == EvaluationStatus.FINDINGS_DETECTED
    assert len(evaluation.findings) == 1
    finding = evaluation.findings[0]
    assert finding.rule_id == "DERA-SCHEMA-002"
    assert finding.severity == DiagnosticSeverity.CRITICAL


def test_rule_002_identity_collision_negative() -> None:
    rule = CanonicalIdentityCollisionRule()
    tbl1 = MockTable(object_id="dera:table:id1", name="table_one")
    tbl2 = MockTable(object_id="dera:table:id2", name="table_two")
    schema = MockSchema(tables=(tbl1, tbl2))
    context = DiagnosticContext(schema=schema)

    evaluation = rule.evaluate(context)
    assert evaluation.status == EvaluationStatus.PASS


# --- DERA-SCHEMA-003 Tests ---


def test_rule_003_invalid_mapping_cardinality_mismatch() -> None:
    rule = InvalidRelationshipMappingRule()
    fk = MockFKRef(
        foreign_key_id="fk_composite",
        foreign_key_name="fk_composite",
        source_table_name="orders",
        referenced_table_name="tenants",
        source_columns=("tenant_id", "order_id"),
        referenced_columns=("id",),  # Mismatch: 2 vs 1
        status="resolved",
    )
    schema = MockSchema(foreign_key_references=(fk,))
    context = DiagnosticContext(schema=schema)

    evaluation = rule.evaluate(context)
    assert evaluation.status == EvaluationStatus.FINDINGS_DETECTED
    assert len(evaluation.findings) == 1
    assert "Mismatched column count" in evaluation.findings[0].title


def test_rule_003_invalid_mapping_empty_columns() -> None:
    rule = InvalidRelationshipMappingRule()
    fk = MockFKRef(
        foreign_key_id="fk_empty",
        foreign_key_name="fk_empty",
        source_table_name="orders",
        referenced_table_name="tenants",
        source_columns=(),
        referenced_columns=(),
        status="resolved",
    )
    schema = MockSchema(foreign_key_references=(fk,))
    context = DiagnosticContext(schema=schema)

    evaluation = rule.evaluate(context)
    assert evaluation.status == EvaluationStatus.FINDINGS_DETECTED
    assert "Empty column mapping" in evaluation.findings[0].title


# --- DERA-SCHEMA-004 Tests ---


def test_rule_004_missing_structural_metadata_positive() -> None:
    rule = MissingStructuralMetadataRule()
    tbl_empty = MockTable(object_id="dera:table:empty_tbl", name="empty_tbl", columns=())
    schema = MockSchema(tables=(tbl_empty,))
    context = DiagnosticContext(schema=schema)

    evaluation = rule.evaluate(context)
    assert evaluation.status == EvaluationStatus.FINDINGS_DETECTED
    assert len(evaluation.findings) == 1
    assert "has no columns" in evaluation.findings[0].title


def test_rule_004_missing_structural_metadata_negative() -> None:
    rule = MissingStructuralMetadataRule()
    col = MockColumn(object_id="dera:col:1", name="id")
    tbl_ok = MockTable(object_id="dera:table:tbl_ok", name="tbl_ok", columns=(col,))
    schema = MockSchema(tables=(tbl_ok,))
    context = DiagnosticContext(schema=schema)

    evaluation = rule.evaluate(context)
    assert evaluation.status == EvaluationStatus.PASS


# --- DERA-SCHEMA-005 Tests ---


def test_rule_005_unsupported_capability_reporting() -> None:
    rule = UnsupportedCapabilityRule()
    profile = MockCapProfile(
        capabilities={
            "check_constraints": "UNSUPPORTED",
            "triggers": "SUPPORTED",
            "generated_columns": "UNTESTED",
        }
    )
    context = DiagnosticContext(capabilities=profile, source_engine="sqlite")

    evaluation = rule.evaluate(context)
    assert evaluation.status == EvaluationStatus.FINDINGS_DETECTED
    # 2 unsupported/untested capabilities: check_constraints and generated_columns
    assert len(evaluation.findings) == 2
    for f in evaluation.findings:
        assert f.severity == DiagnosticSeverity.INFORMATIONAL
