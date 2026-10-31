"""Tests for DERA diagnostic engine security invariants, resource limits, and data sanitization."""

from __future__ import annotations

from dataclasses import dataclass

import pytest
from dera.diagnostics.context import (
    DiagnosticContext,
    DiagnosticEngineConfig,
    DiagnosticResourceLimits,
)
from dera.diagnostics.enums import (
    DiagnosticSeverity,
    EvaluationStatus,
    RuleCategory,
)
from dera.diagnostics.evaluator import DiagnosticEvaluator
from dera.diagnostics.evidence import DiagnosticEvidence, sanitize_value
from dera.diagnostics.exceptions import ResourceLimitExceededError
from dera.diagnostics.models import (
    DiagnosticFinding,
    RuleEvaluation,
    RuleMetadata,
)


@dataclass
class DummyObject:
    object_id: str
    name: str
    columns: tuple = ()


@dataclass
class DummySchema:
    tables: tuple[DummyObject, ...] = ()
    views: tuple[DummyObject, ...] = ()
    namespaces: tuple[DummyObject, ...] = ()


def test_sensitive_credential_sanitization() -> None:
    """Verifies that credentials and secrets are stripped from evidence dictionary representations."""
    raw = {
        "url": "postgres://admin:top_secret_pass@db.dera.internal:5432/main",
        "api_key": "sk-1234567890abcdef",
        "nested": {"token": "bearer_jwt_secret", "normal_field": "public_data"},
    }

    sanitized = sanitize_value(raw)
    assert "top_secret_pass" not in str(sanitized)
    assert sanitized["api_key"] == "[REDACTED]"
    assert sanitized["nested"]["token"] == "[REDACTED]"
    assert sanitized["nested"]["normal_field"] == "public_data"


def test_resource_limit_object_ceiling() -> None:
    """Verifies that attempting to evaluate a schema with excessive objects is rejected."""
    tables = tuple(DummyObject(f"dera:table:{i}", f"table_{i}") for i in range(105))
    schema = DummySchema(tables=tables)

    limits = DiagnosticResourceLimits(max_objects=100)
    config = DiagnosticEngineConfig(limits=limits)
    context = DiagnosticContext(schema=schema, config=config)  # type: ignore[arg-type]

    evaluator = DiagnosticEvaluator()

    with pytest.raises(ResourceLimitExceededError) as exc_info:
        evaluator.evaluate(context, [])

    assert exc_info.value.resource == "objects"
    assert exc_info.value.current == 105
    assert exc_info.value.limit == 100


def test_resource_limit_finding_ceiling() -> None:
    """Verifies that an evaluation runaway producing excessive findings is aborted."""

    class ProlificRule:
        def __init__(self) -> None:
            self._metadata = RuleMetadata(
                rule_id="DERA-PROLIFIC-001",
                title="Prolific Finding Generator",
                description="Produces findings",
                version="1.0.0",
                category=RuleCategory.STRUCTURAL_INTEGRITY,
                default_severity=DiagnosticSeverity.LOW,
                supported_object_kinds=("table",),
            )

        @property
        def metadata(self) -> RuleMetadata:
            return self._metadata

        def evaluate(self, context: DiagnosticContext) -> RuleEvaluation:
            findings = tuple(
                DiagnosticFinding(
                    rule_id=self.metadata.rule_id,
                    rule_version=self.metadata.version,
                    object_id=f"dera:table:{i}",
                    severity=self.metadata.default_severity,
                    title=f"Finding {i}",
                    description=f"Description {i}",
                    evidence=(
                        DiagnosticEvidence(
                            object_id=f"dera:table:{i}",
                            field_name="f",
                            observed_value=i,
                        ),
                    ),
                    severity_rationale="Rationale",
                )
                for i in range(25)
            )
            return RuleEvaluation(
                rule_id=self.metadata.rule_id,
                rule_version=self.metadata.version,
                status=EvaluationStatus.FINDINGS_DETECTED,
                findings=findings,
            )

    limits = DiagnosticResourceLimits(max_findings=10)
    config = DiagnosticEngineConfig(limits=limits)
    context = DiagnosticContext(config=config)
    evaluator = DiagnosticEvaluator()

    with pytest.raises(ResourceLimitExceededError) as exc_info:
        evaluator.evaluate(context, [ProlificRule()])

    assert exc_info.value.resource == "findings"
