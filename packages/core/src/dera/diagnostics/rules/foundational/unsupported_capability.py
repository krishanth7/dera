"""DERA Diagnostics — Rule DERA-SCHEMA-005: Unsupported Inspection Capability.

Identifies metadata capabilities that are unsupported or untested by the
underlying database connector or source engine, providing transparent coverage
reporting without creating false-positive defect findings.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from dera.diagnostics.enums import (
    DiagnosticSeverity,
    EvaluationStatus,
    RuleCategory,
)
from dera.diagnostics.evidence import DiagnosticEvidence
from dera.diagnostics.models import (
    DiagnosticFinding,
    RuleEvaluation,
    RuleMetadata,
)

if TYPE_CHECKING:
    from dera.diagnostics.context import DiagnosticContext


class UnsupportedCapabilityRule:
    """Audits capability profiles and reports uninspected database feature areas."""

    def __init__(self) -> None:
        self._metadata = RuleMetadata(
            rule_id="DERA-SCHEMA-005",
            title="Unsupported Inspection Capability",
            description=(
                "Reports schema feature areas (e.g. check constraints, triggers, generated columns) "
                "that the connector or database engine does not support, informing diagnostic coverage."
            ),
            version="1.0.0",
            category=RuleCategory.METADATA_COMPLETENESS,
            default_severity=DiagnosticSeverity.INFORMATIONAL,
            supported_object_kinds=("database",),
            required_capabilities=(),
            applicability_summary="Applies to contexts with a SchemaCapabilityProfile.",
            evidence_requirements="Requires capability profile entries and capability states.",
            recommendation_template=(
                "Capability '{capability_name}' is not supported by connector for engine '{engine}'. "
                "Diagnostic checks requiring this capability will be skipped."
            ),
            documentation_url="https://docs.dera.dev/diagnostics/rules/DERA-SCHEMA-005",
        )

    @property
    def metadata(self) -> RuleMetadata:
        return self._metadata

    def evaluate(self, context: DiagnosticContext) -> RuleEvaluation:
        start_time = time.perf_counter()
        capabilities = context.capabilities
        engine = context.source_engine

        if capabilities is None:
            return RuleEvaluation(
                rule_id=self.metadata.rule_id,
                rule_version=self.metadata.version,
                status=EvaluationStatus.INSUFFICIENT_METADATA,
                findings=(),
                execution_duration_ms=(time.perf_counter() - start_time) * 1000,
                message="No schema capability profile provided in diagnostic context.",
            )

        unsupported_capabilities: list[tuple[str, str]] = []  # (cap_name, state)
        for cap_name, cap_state in capabilities.capabilities.items():
            state_str = getattr(cap_state, "value", str(cap_state))
            if state_str in ("UNSUPPORTED", "UNTESTED", "FAILED"):
                unsupported_capabilities.append((cap_name, state_str))

        findings: list[DiagnosticFinding] = []
        for cap_name, state_str in unsupported_capabilities:
            evidence = (
                DiagnosticEvidence(
                    object_id=f"dera:capability:{cap_name}",
                    field_name="capability_state",
                    observed_value=state_str,
                    expected_value="SUPPORTED",
                    message=(
                        f"Capability '{cap_name}' for engine '{engine}' has state '{state_str}'."
                    ),
                    context_data={
                        "capability_name": cap_name,
                        "source_engine": engine,
                        "state": state_str,
                    },
                ),
            )

            finding = DiagnosticFinding(
                rule_id=self.metadata.rule_id,
                rule_version=self.metadata.version,
                object_id=f"dera:capability:{cap_name}",
                severity=self.metadata.default_severity,
                title=f"Capability '{cap_name}' unsupported or uninspected",
                description=(
                    f"The current inspection profile indicates that '{cap_name}' is '{state_str}' "
                    f"for database engine '{engine}'."
                ),
                evidence=evidence,
                severity_rationale=(
                    "Informational diagnostic coverage notice; does not constitute a schema defect."
                ),
                recommendation=self.metadata.recommendation_template.format(
                    capability_name=cap_name,
                    engine=engine,
                ),
            )
            findings.append(finding)

        elapsed = (time.perf_counter() - start_time) * 1000

        if findings:
            return RuleEvaluation(
                rule_id=self.metadata.rule_id,
                rule_version=self.metadata.version,
                status=EvaluationStatus.FINDINGS_DETECTED,
                findings=tuple(findings),
                execution_duration_ms=elapsed,
                message=f"Reported {len(findings)} unsupported or uninspected capabilities.",
            )

        return RuleEvaluation(
            rule_id=self.metadata.rule_id,
            rule_version=self.metadata.version,
            status=EvaluationStatus.PASS,
            findings=(),
            execution_duration_ms=elapsed,
            message="All standard schema inspection capabilities are fully supported.",
        )
