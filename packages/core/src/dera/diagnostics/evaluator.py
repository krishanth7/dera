"""DERA Diagnostics — Evaluation Orchestrator.

Orchestrates deterministic rule execution, resource limit enforcement,
error isolation, and diagnostic report aggregation without AI or external dependencies.
"""

from __future__ import annotations

import time
import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from dera.diagnostics.applicability import check_rule_applicability
from dera.diagnostics.enums import (
    ApplicabilityStatus,
    DiagnosticSeverity,
    EvaluationStatus,
)
from dera.diagnostics.exceptions import ResourceLimitExceededError
from dera.diagnostics.fingerprint import (
    compute_config_fingerprint,
)
from dera.diagnostics.models import (
    DiagnosticCoverage,
    DiagnosticFinding,
    DiagnosticReport,
    DiagnosticSummaryCounts,
    RuleEvaluation,
)
from dera.diagnostics.serialization import compute_report_content_hash

if TYPE_CHECKING:
    from collections.abc import Iterable

    from dera.diagnostics.context import DiagnosticContext
    from dera.diagnostics.protocols import DiagnosticRule


class DiagnosticEvaluator:
    """Deterministic orchestrator for executing diagnostic rules against schema contexts."""

    def __init__(self, rule_set_version: str = "1.0.0") -> None:
        self.rule_set_version = rule_set_version

    def evaluate(
        self,
        context: DiagnosticContext,
        rules: Iterable[DiagnosticRule],
    ) -> DiagnosticReport:
        """Evaluates rules against context and produces an immutable DiagnosticReport.

        Guarantees:
          - Deterministic rule sorting by rule_id.
          - Deterministic finding sorting by (severity.rank DESC, object_id, rule_id, fingerprint).
          - Error isolation: an exception in one rule produces an EVALUATION_ERROR outcome without aborting others.
          - Enforced resource limits for objects, edges, and findings.
        """
        limits = context.config.limits
        schema = context.schema
        if schema is None and context.snapshot is not None:
            schema = getattr(context.snapshot, "schema_representation", None)

        # 1. Enforce object count limit
        if schema is not None:
            total_objects = (
                len(getattr(schema, "tables", ()))
                + len(getattr(schema, "views", ()))
                + len(getattr(schema, "namespaces", ()))
            )
            if total_objects > limits.max_objects:
                raise ResourceLimitExceededError("objects", total_objects, limits.max_objects)

        # 2. Enforce edge count limit
        if context.graph is not None:
            edge_count = len(getattr(context.graph, "edges", ()))
            if edge_count > limits.max_edges:
                raise ResourceLimitExceededError("edges", edge_count, limits.max_edges)

        # 3. Sort rules deterministically by rule_id
        sorted_rules = sorted(rules, key=lambda r: r.metadata.rule_id)

        evaluations: list[RuleEvaluation] = []
        all_findings: list[DiagnosticFinding] = []

        evaluated_rule_ids: list[str] = []
        skipped_rule_ids: list[str] = []
        unsupported_rule_ids: list[str] = []
        insufficient_metadata_rule_ids: list[str] = []
        errored_rule_ids: list[str] = []

        findings_by_severity: dict[str, int] = {s.value: 0 for s in DiagnosticSeverity}

        # 4. Sequential deterministic rule execution
        for rule in sorted_rules:
            rule_id = rule.metadata.rule_id
            rule_version = rule.metadata.version

            # Check rule applicability
            app_status, reason = check_rule_applicability(rule, context)

            if app_status == ApplicabilityStatus.NOT_APPLICABLE:
                skipped_rule_ids.append(rule_id)
                evaluations.append(
                    RuleEvaluation(
                        rule_id=rule_id,
                        rule_version=rule_version,
                        status=EvaluationStatus.NOT_APPLICABLE,
                        message=reason,
                    )
                )
                continue

            if app_status == ApplicabilityStatus.UNSUPPORTED:
                unsupported_rule_ids.append(rule_id)
                evaluations.append(
                    RuleEvaluation(
                        rule_id=rule_id,
                        rule_version=rule_version,
                        status=EvaluationStatus.UNSUPPORTED,
                        message=reason,
                    )
                )
                continue

            if app_status == ApplicabilityStatus.INSUFFICIENT_METADATA:
                insufficient_metadata_rule_ids.append(rule_id)
                evaluations.append(
                    RuleEvaluation(
                        rule_id=rule_id,
                        rule_version=rule_version,
                        status=EvaluationStatus.INSUFFICIENT_METADATA,
                        message=reason,
                    )
                )
                continue

            # Execute rule with error isolation
            evaluated_rule_ids.append(rule_id)
            rule_start = time.perf_counter()
            try:
                evaluation = rule.evaluate(context)
                evaluations.append(evaluation)

                if evaluation.status == EvaluationStatus.FINDINGS_DETECTED:
                    for f in evaluation.findings:
                        if len(all_findings) >= limits.max_findings:
                            raise ResourceLimitExceededError(
                                "findings", len(all_findings) + 1, limits.max_findings
                            )
                        all_findings.append(f)
                        sev_str = f.severity.value
                        findings_by_severity[sev_str] = findings_by_severity.get(sev_str, 0) + 1

                elif evaluation.status == EvaluationStatus.INSUFFICIENT_METADATA:
                    insufficient_metadata_rule_ids.append(rule_id)
                elif evaluation.status == EvaluationStatus.UNSUPPORTED:
                    unsupported_rule_ids.append(rule_id)
                elif evaluation.status == EvaluationStatus.EVALUATION_ERROR:
                    errored_rule_ids.append(rule_id)

            except ResourceLimitExceededError:
                raise
            except Exception as exc:
                errored_rule_ids.append(rule_id)
                duration_ms = (time.perf_counter() - rule_start) * 1000
                evaluations.append(
                    RuleEvaluation(
                        rule_id=rule_id,
                        rule_version=rule_version,
                        status=EvaluationStatus.EVALUATION_ERROR,
                        findings=(),
                        execution_duration_ms=duration_ms,
                        message=f"Rule execution failed: {type(exc).__name__}",
                        error_details=f"{type(exc).__name__}: {exc}",
                    )
                )

        # 5. Deterministic sorting of findings
        # Tuple: (severity.rank DESC, object_id ASC, rule_id ASC, fingerprint ASC)
        sorted_findings = sorted(
            all_findings,
            key=lambda f: (-f.severity.rank, f.object_id, f.rule_id, f.fingerprint),
        )

        # 6. Build summary counts & coverage
        passed_count = sum(1 for e in evaluations if e.status == EvaluationStatus.PASS)
        findings_count = sum(
            1 for e in evaluations if e.status == EvaluationStatus.FINDINGS_DETECTED
        )
        skipped_count = len(skipped_rule_ids)
        unsupported_count = len(unsupported_rule_ids)
        insufficient_count = len(insufficient_metadata_rule_ids)
        errored_count = len(errored_rule_ids)

        summary = DiagnosticSummaryCounts(
            total_rules_evaluated=len(evaluated_rule_ids),
            rules_passed=passed_count,
            rules_with_findings=findings_count,
            rules_skipped=skipped_count,
            rules_unsupported=unsupported_count,
            rules_insufficient_metadata=insufficient_count,
            rules_errored=errored_count,
            total_findings=len(sorted_findings),
            findings_by_severity=findings_by_severity,
        )

        coverage = DiagnosticCoverage(
            evaluated_rules=tuple(evaluated_rule_ids),
            skipped_rules=tuple(skipped_rule_ids),
            unsupported_rules=tuple(unsupported_rule_ids),
            insufficient_metadata_rules=tuple(insufficient_metadata_rule_ids),
            errored_rules=tuple(errored_rule_ids),
        )

        config_fingerprint = compute_config_fingerprint(context.config.to_canonical_dict())
        eval_id = f"eval_{uuid.uuid4().hex[:16]}"
        eval_time = datetime.now(UTC).isoformat()

        report_dict = {
            "snapshot_id": context.snapshot_id,
            "rule_set_version": self.rule_set_version,
            "config_fingerprint": config_fingerprint,
            "source_engine": context.source_engine,
            "summary": summary.to_canonical_dict(),
            "coverage": coverage.to_canonical_dict(),
            "findings": [f.to_canonical_dict() for f in sorted_findings],
            "rule_evaluations": [e.to_canonical_dict() for e in evaluations],
        }
        report_hash = compute_report_content_hash(report_dict)

        return DiagnosticReport(
            evaluation_id=eval_id,
            evaluated_at=eval_time,
            snapshot_id=context.snapshot_id,
            rule_set_version=self.rule_set_version,
            config_fingerprint=config_fingerprint,
            findings=tuple(sorted_findings),
            rule_evaluations=tuple(evaluations),
            summary=summary,
            coverage=coverage,
            source_engine=context.source_engine,
            report_hash=report_hash,
        )
