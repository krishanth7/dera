"""DERA Diagnostics — Evaluation Orchestrator.

Orchestrates deterministic rule execution, resource limit enforcement,
error isolation, evidence validation, severity derivation, recommendation generation,
suppression governance, prioritization, and explainable report aggregation without AI or external dependencies.
"""

from __future__ import annotations

import time
import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from dera.diagnostics.applicability import check_rule_applicability
from dera.diagnostics.enums import (
    ApplicabilityStatus,
    DiagnosticSeverity,
    EvaluationStatus,
    RuleCategory,
)
from dera.diagnostics.evidence.validator import validate_and_enrich_evidence
from dera.diagnostics.exceptions import ResourceLimitExceededError
from dera.diagnostics.fingerprint import compute_config_fingerprint
from dera.diagnostics.governance.lifecycle import FindingLifecycleState
from dera.diagnostics.governance.suppressions import DiagnosticSuppression
from dera.diagnostics.models import (
    DiagnosticCoverage,
    DiagnosticFinding,
    DiagnosticReport,
    DiagnosticSummaryCounts,
    RuleEvaluation,
)
from dera.diagnostics.prioritization.classification import classify_rule_finding
from dera.diagnostics.prioritization.ordering import sort_findings_deterministically
from dera.diagnostics.prioritization.ranking import (
    compute_priority_score,
    derive_priority_rank,
)
from dera.diagnostics.recommendations.catalog import RECOMMENDATION_CATALOG_VERSION
from dera.diagnostics.recommendations.generator import generate_structured_recommendation
from dera.diagnostics.reports.explainability import build_report_explainability
from dera.diagnostics.serialization import compute_report_content_hash
from dera.diagnostics.severity.overrides import SeverityOverride
from dera.diagnostics.severity.policy import (
    SEVERITY_POLICY_VERSION,
    derive_effective_severity,
)
from dera.diagnostics.severity.rationale import build_severity_rationale

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
          - Evidence validation, credential sanitization, and reference integrity.
          - Conservative severity derivation and authorized override application.
          - Deterministic, advisory engineering recommendation generation.
          - Transparent suppression governance (suppressed findings remain auditable).
          - Deterministic 6-element finding prioritization.
          - Complete report explainability and cryptographic hash verification.
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
        raw_findings: list[DiagnosticFinding] = []

        evaluated_rule_ids: list[str] = []
        skipped_rule_ids: list[str] = []
        unsupported_rule_ids: list[str] = []
        insufficient_metadata_rule_ids: list[str] = []
        errored_rule_ids: list[str] = []

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
                        if len(raw_findings) >= limits.max_findings:
                            raise ResourceLimitExceededError(
                                "findings", len(raw_findings) + 1, limits.max_findings
                            )
                        raw_findings.append(f)

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

        # 5. Extract suppressions and overrides from configuration
        active_suppressions: list[DiagnosticSuppression] = [
            s
            for s in getattr(context.config, "suppressions", ())
            if isinstance(s, DiagnosticSuppression) and s.is_active()
        ]
        overrides_by_fingerprint: dict[str, SeverityOverride] = {
            o.finding_fingerprint: o
            for o in getattr(context.config, "severity_overrides", ())
            if isinstance(o, SeverityOverride)
        }

        # 6. Phase 8.5 Post-Processing: Evidence, Severity, Recommendations, Governance
        unified_findings: list[DiagnosticFinding] = []
        applied_suppressions: list[dict[str, Any]] = []
        applied_overrides: list[dict[str, Any]] = []
        findings_by_severity: dict[str, int] = {s.value: 0 for s in DiagnosticSeverity}

        rule_category_map: dict[str, RuleCategory] = {
            r.metadata.rule_id: r.metadata.category for r in sorted_rules
        }

        for raw_f in raw_findings:
            # 6.1 Validate and enrich evidence
            ev_result = validate_and_enrich_evidence(raw_f.evidence, context)

            # 6.2 Classify finding
            classification = classify_rule_finding(raw_f.rule_id)

            # 6.3 Severity evaluation
            effective_sev, policy_reason = derive_effective_severity(
                rule_id=raw_f.rule_id,
                default_severity=raw_f.severity,
                classification=classification,
                completeness=ev_result.completeness,
                confidence=ev_result.confidence,
            )

            # Check authorized override
            override_id = None
            if raw_f.fingerprint in overrides_by_fingerprint:
                override = overrides_by_fingerprint[raw_f.fingerprint]
                effective_sev = override.effective_severity
                override_id = override.override_id
                applied_overrides.append(override.to_canonical_dict())
                policy_reason += f" Overridden by authorized actor '{override.authorized_actor}': {override.override_reason}."

            # Build severity rationale
            rationale = build_severity_rationale(
                rule_id=raw_f.rule_id,
                original_severity=raw_f.severity,
                effective_severity=effective_sev,
                classification=classification,
                confidence=ev_result.confidence,
                completeness=ev_result.completeness,
                rule_reason=policy_reason,
            )

            # 6.4 Deterministic recommendation assembly
            structured_rec = generate_structured_recommendation(raw_f)
            rec_text = structured_rec.suggested_action if structured_rec else raw_f.recommendation

            # 6.5 Suppression matching
            is_suppressed = False
            suppression_id = None
            lifecycle_state = FindingLifecycleState.OPEN

            for sup in active_suppressions:
                if sup.matches(raw_f):
                    is_suppressed = True
                    suppression_id = sup.suppression_id
                    lifecycle_state = FindingLifecycleState.SUPPRESSED
                    applied_suppressions.append(sup.to_canonical_dict())
                    break

            # 6.6 Prioritization score and rank
            priority_score = compute_priority_score(
                severity=effective_sev,
                confidence=ev_result.confidence,
                classification=classification,
            )
            priority_rank = derive_priority_rank(effective_sev)

            rule_cat = rule_category_map.get(raw_f.rule_id, RuleCategory.STRUCTURAL_INTEGRITY)

            # 6.7 Assemble enriched finding
            enriched_finding = DiagnosticFinding(
                rule_id=raw_f.rule_id,
                rule_version=raw_f.rule_version,
                object_id=raw_f.object_id,
                severity=effective_sev,
                title=raw_f.title,
                description=raw_f.description,
                evidence=tuple(ev_result.validated_evidence),
                severity_rationale=rationale,
                recommendation=rec_text,
                fingerprint=raw_f.fingerprint,
                category=rule_cat,
                classification=classification,
                original_severity=raw_f.severity,
                confidence=ev_result.confidence,
                metadata_completeness=ev_result.completeness,
                structured_recommendation=structured_rec,
                lifecycle_state=lifecycle_state,
                is_suppressed=is_suppressed,
                suppression_id=suppression_id,
                override_id=override_id,
                priority_score=priority_score,
                priority_rank=priority_rank,
            )
            unified_findings.append(enriched_finding)

            sev_str = effective_sev.value
            findings_by_severity[sev_str] = findings_by_severity.get(sev_str, 0) + 1

        # 7. Deterministic multi-factor sorting of findings
        sorted_findings = sort_findings_deterministically(unified_findings)

        # 8. Build summary counts & coverage
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

        # 9. Build Report Explainability
        explainability = build_report_explainability(
            summary=summary,
            coverage=coverage,
            evaluations=evaluations,
            findings=sorted_findings,
            rule_set_version=self.rule_set_version,
            severity_policy_version=SEVERITY_POLICY_VERSION,
            recommendation_catalog_version=RECOMMENDATION_CATALOG_VERSION,
            config_fingerprint=config_fingerprint,
        )

        report_dict = {
            "snapshot_id": context.snapshot_id,
            "rule_set_version": self.rule_set_version,
            "severity_policy_version": SEVERITY_POLICY_VERSION,
            "recommendation_catalog_version": RECOMMENDATION_CATALOG_VERSION,
            "config_fingerprint": config_fingerprint,
            "source_engine": context.source_engine,
            "summary": summary.to_canonical_dict(),
            "coverage": coverage.to_canonical_dict(),
            "explainability": explainability.to_canonical_dict(),
            "suppressions_applied": applied_suppressions,
            "severity_overrides_applied": applied_overrides,
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
            explainability=explainability,
            severity_policy_version=SEVERITY_POLICY_VERSION,
            recommendation_catalog_version=RECOMMENDATION_CATALOG_VERSION,
            suppressions_applied=tuple(applied_suppressions),
            severity_overrides_applied=tuple(applied_overrides),
        )
