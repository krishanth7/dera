"""Tests for DERA diagnostic evaluation orchestrator, error isolation, and resource bounding."""

from __future__ import annotations

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
from dera.diagnostics.evidence import DiagnosticEvidence
from dera.diagnostics.exceptions import ResourceLimitExceededError
from dera.diagnostics.models import (
    DiagnosticFinding,
    RuleEvaluation,
    RuleMetadata,
)


class MockPassingRule:
    def __init__(self, rule_id: str) -> None:
        self._metadata = RuleMetadata(
            rule_id=rule_id,
            title=f"Passing rule {rule_id}",
            description="Mock pass",
            version="1.0.0",
            category=RuleCategory.STRUCTURAL_INTEGRITY,
            default_severity=DiagnosticSeverity.LOW,
            supported_object_kinds=("table",),
        )

    @property
    def metadata(self) -> RuleMetadata:
        return self._metadata

    def evaluate(self, context: DiagnosticContext) -> RuleEvaluation:
        return RuleEvaluation(
            rule_id=self.metadata.rule_id,
            rule_version=self.metadata.version,
            status=EvaluationStatus.PASS,
            message="Passed successfully.",
        )


class MockFindingRule:
    def __init__(
        self, rule_id: str, severity: DiagnosticSeverity = DiagnosticSeverity.HIGH
    ) -> None:
        self._metadata = RuleMetadata(
            rule_id=rule_id,
            title=f"Finding rule {rule_id}",
            description="Mock finding",
            version="1.0.0",
            category=RuleCategory.RELATIONSHIPS,
            default_severity=severity,
            supported_object_kinds=("table",),
        )

    @property
    def metadata(self) -> RuleMetadata:
        return self._metadata

    def evaluate(self, context: DiagnosticContext) -> RuleEvaluation:
        finding = DiagnosticFinding(
            rule_id=self.metadata.rule_id,
            rule_version=self.metadata.version,
            object_id="dera:table:orders",
            severity=self.metadata.default_severity,
            title="Mock Defect",
            description="Defect observed",
            evidence=(
                DiagnosticEvidence(
                    object_id="dera:table:orders",
                    field_name="mock_col",
                    observed_value="bad",
                ),
            ),
            severity_rationale="High impact",
        )
        return RuleEvaluation(
            rule_id=self.metadata.rule_id,
            rule_version=self.metadata.version,
            status=EvaluationStatus.FINDINGS_DETECTED,
            findings=(finding,),
            message="1 finding detected.",
        )


class MockCrashingRule:
    def __init__(self, rule_id: str) -> None:
        self._metadata = RuleMetadata(
            rule_id=rule_id,
            title=f"Crashing rule {rule_id}",
            description="Simulates unexpected unhandled crash",
            version="1.0.0",
            category=RuleCategory.DEPENDENCIES,
            default_severity=DiagnosticSeverity.MEDIUM,
            supported_object_kinds=("table",),
        )

    @property
    def metadata(self) -> RuleMetadata:
        return self._metadata

    def evaluate(self, context: DiagnosticContext) -> RuleEvaluation:
        raise ZeroDivisionError("Simulated unhandled internal mathematical error!")


def test_evaluator_error_isolation() -> None:
    """Verifies that an exception in one rule is isolated and does not abort evaluation."""
    evaluator = DiagnosticEvaluator()
    context = DiagnosticContext()

    rule_pass = MockPassingRule("DERA-PASS-001")
    rule_crash = MockCrashingRule("DERA-CRASH-002")
    rule_finding = MockFindingRule("DERA-FIND-003")

    report = evaluator.evaluate(context, [rule_pass, rule_crash, rule_finding])

    # Overall report must complete
    assert report.summary.total_rules_evaluated == 3
    assert report.summary.rules_passed == 1
    assert report.summary.rules_with_findings == 1
    assert report.summary.rules_errored == 1
    assert "DERA-CRASH-002" in report.coverage.errored_rules

    # Verify crashing evaluation details
    crash_eval = next(e for e in report.rule_evaluations if e.rule_id == "DERA-CRASH-002")
    assert crash_eval.status == EvaluationStatus.EVALUATION_ERROR
    assert "ZeroDivisionError" in str(crash_eval.error_details)


def test_evaluator_finding_limit_enforcement() -> None:
    """Verifies that exceeding max_findings raises ResourceLimitExceededError."""
    evaluator = DiagnosticEvaluator()
    limits = DiagnosticResourceLimits(max_findings=1)
    config = DiagnosticEngineConfig(limits=limits)
    context = DiagnosticContext(config=config)

    rule1 = MockFindingRule("DERA-FIND-001")
    rule2 = MockFindingRule("DERA-FIND-002")

    with pytest.raises(ResourceLimitExceededError) as exc_info:
        evaluator.evaluate(context, [rule1, rule2])

    assert exc_info.value.resource == "findings"


def test_evaluator_deterministic_severity_ordering() -> None:
    """Verifies findings are sorted by severity rank descending, then object ID, rule ID."""
    evaluator = DiagnosticEvaluator()
    context = DiagnosticContext()

    rule_low = MockFindingRule("DERA-R-LOW", severity=DiagnosticSeverity.LOW)
    rule_crit = MockFindingRule("DERA-R-CRIT", severity=DiagnosticSeverity.CRITICAL)
    rule_med = MockFindingRule("DERA-R-MED", severity=DiagnosticSeverity.MEDIUM)

    report = evaluator.evaluate(context, [rule_low, rule_crit, rule_med])

    severities = [f.severity for f in report.findings]
    assert severities == [
        DiagnosticSeverity.CRITICAL,
        DiagnosticSeverity.MEDIUM,
        DiagnosticSeverity.LOW,
    ]
