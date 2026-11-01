"""DERA API — Phase 8.1 Schema Diagnostic Endpoints.

Provides authorized endpoints for listing versioned diagnostic rules, inspecting
rule metadata, and executing deterministic diagnostic evaluations against canonical schemas.
"""

from __future__ import annotations

from typing import Annotated

from dera.diagnostics import DiagnosticEngineConfig
from fastapi import APIRouter, Depends, HTTPException, status

from dera_api.api.v1.endpoints.reverse_engineering.deps import (
    get_re_service,
    resolve_authorized_workspace_id,
)
from dera_api.api.v1.endpoints.reverse_engineering.service import ReverseEngineeringService
from dera_api.contracts.errors import ProblemDetail
from dera_api.schemas.reverse_engineering import (
    DiagnosticEvaluateRequest,
    DiagnosticEvaluationResponse,
    DiagnosticEvidenceResponse,
    DiagnosticFindingResponse,
    DiagnosticReportResponse,
    DiagnosticRuleMetadataResponse,
)

router = APIRouter()


@router.get(
    "/diagnostics/rules",
    response_model=list[DiagnosticRuleMetadataResponse],
    status_code=status.HTTP_200_OK,
    summary="List available diagnostic rules",
    responses={
        200: {
            "model": list[DiagnosticRuleMetadataResponse],
            "description": "Deterministic catalog of available diagnostic rules.",
        },
        401: {"model": ProblemDetail, "description": "Authentication required."},
    },
)
async def list_diagnostic_rules(
    service: Annotated[ReverseEngineeringService, Depends(get_re_service)],
) -> list[DiagnosticRuleMetadataResponse]:
    """Retrieves all registered diagnostic rules sorted deterministically by rule ID."""
    rules = service.list_diagnostic_rules()
    return [
        DiagnosticRuleMetadataResponse(
            rule_id=meta.rule_id,
            title=meta.title,
            description=meta.description,
            version=meta.version,
            category=meta.category.value,
            default_severity=meta.default_severity.value,
            supported_object_kinds=list(meta.supported_object_kinds),
            required_capabilities=list(meta.required_capabilities),
            supported_engines=list(meta.supported_engines),
            documentation_url=meta.documentation_url,
        )
        for meta in rules
    ]


@router.get(
    "/diagnostics/rules/{rule_id}",
    response_model=DiagnosticRuleMetadataResponse,
    status_code=status.HTTP_200_OK,
    summary="Get diagnostic rule metadata",
    responses={
        200: {
            "model": DiagnosticRuleMetadataResponse,
            "description": "Rule metadata details.",
        },
        401: {"model": ProblemDetail, "description": "Authentication required."},
        404: {"model": ProblemDetail, "description": "Rule not found in registry."},
    },
)
async def get_diagnostic_rule(
    rule_id: str,
    service: Annotated[ReverseEngineeringService, Depends(get_re_service)],
) -> DiagnosticRuleMetadataResponse:
    """Retrieves declared metadata for a specific diagnostic rule ID."""
    meta = service.get_diagnostic_rule(rule_id)
    if meta is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Diagnostic rule '{rule_id}' was not found in the registry.",
        )

    return DiagnosticRuleMetadataResponse(
        rule_id=meta.rule_id,
        title=meta.title,
        description=meta.description,
        version=meta.version,
        category=meta.category.value,
        default_severity=meta.default_severity.value,
        supported_object_kinds=list(meta.supported_object_kinds),
        required_capabilities=list(meta.required_capabilities),
        supported_engines=list(meta.supported_engines),
        documentation_url=meta.documentation_url,
    )


@router.post(
    "/schemas/{schema_id}/diagnostics",
    response_model=DiagnosticReportResponse,
    status_code=status.HTTP_200_OK,
    summary="Evaluate diagnostic rules against schema",
    responses={
        200: {
            "model": DiagnosticReportResponse,
            "description": "Deterministic diagnostic report.",
        },
        401: {"model": ProblemDetail, "description": "Authentication required."},
        403: {"model": ProblemDetail, "description": "Workspace access denied."},
        404: {"model": ProblemDetail, "description": "Target schema not found."},
    },
)
async def evaluate_schema_diagnostics(
    schema_id: str,
    workspace_id: Annotated[str, Depends(resolve_authorized_workspace_id)],
    service: Annotated[ReverseEngineeringService, Depends(get_re_service)],
    payload: DiagnosticEvaluateRequest | None = None,
) -> DiagnosticReportResponse:
    """Executes deterministic diagnostic rules against an authorized canonical schema."""
    config = None
    if payload is not None:
        enabled = frozenset(payload.enabled_rule_ids) if payload.enabled_rule_ids else None
        disabled = frozenset(payload.disabled_rule_ids)

        from dera.diagnostics.enums import DiagnosticSeverity
        from dera.diagnostics.governance import (
            DiagnosticSuppression,
            SuppressionScope,
            SuppressionStatus,
        )
        from dera.diagnostics.severity import SeverityOverride

        parsed_suppressions: list[DiagnosticSuppression] = []
        for s in payload.suppressions:
            if isinstance(s, DiagnosticSuppression):
                parsed_suppressions.append(s)
            elif isinstance(s, dict):
                try:
                    scope_raw = s.get("scope", SuppressionScope.FINGERPRINT.value)
                    scope_val = (
                        scope_raw
                        if isinstance(scope_raw, SuppressionScope)
                        else SuppressionScope(scope_raw)
                    )
                    status_raw = s.get("status", SuppressionStatus.ACTIVE.value)
                    status_val = (
                        status_raw
                        if isinstance(status_raw, SuppressionStatus)
                        else SuppressionStatus(status_raw)
                    )
                    parsed_suppressions.append(
                        DiagnosticSuppression(
                            suppression_id=s.get("suppression_id", ""),
                            scope=scope_val,
                            reason=s.get("reason", ""),
                            authorized_actor=s.get("authorized_actor", ""),
                            created_at=s.get("created_at", ""),
                            rule_id=s.get("rule_id"),
                            fingerprint=s.get("fingerprint"),
                            scoped_object_id=s.get("scoped_object_id"),
                            expires_at=s.get("expires_at"),
                            status=status_val,
                            notes=s.get("notes", ""),
                        )
                    )
                except Exception:
                    continue

        parsed_overrides: list[SeverityOverride] = []
        for o in payload.severity_overrides:
            if isinstance(o, SeverityOverride):
                parsed_overrides.append(o)
            elif isinstance(o, dict):
                try:
                    orig_sev = o.get("original_severity")
                    orig_sev_val = (
                        orig_sev
                        if isinstance(orig_sev, DiagnosticSeverity)
                        else DiagnosticSeverity(orig_sev)
                    )
                    eff_sev = o.get("effective_severity")
                    eff_sev_val = (
                        eff_sev
                        if isinstance(eff_sev, DiagnosticSeverity)
                        else DiagnosticSeverity(eff_sev)
                    )
                    parsed_overrides.append(
                        SeverityOverride(
                            override_id=o.get("override_id", ""),
                            finding_fingerprint=o.get("finding_fingerprint", ""),
                            original_severity=orig_sev_val,
                            effective_severity=eff_sev_val,
                            override_reason=o.get("override_reason", ""),
                            authorized_actor=o.get("authorized_actor", ""),
                            timestamp=o.get("timestamp", ""),
                            policy_version=o.get("policy_version", "1.0.0"),
                        )
                    )
                except Exception:
                    continue

        config = DiagnosticEngineConfig(
            enabled_rule_ids=enabled,
            disabled_rule_ids=disabled,
            suppressions=tuple(parsed_suppressions),
            severity_overrides=tuple(parsed_overrides),
        )

    report = service.evaluate_diagnostics(
        workspace_id=workspace_id,
        schema_id=schema_id,
        config=config,
    )

    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Schema '{schema_id}' was not found in authorized workspace.",
        )

    findings_resp = [
        DiagnosticFindingResponse(
            fingerprint=f.fingerprint,
            rule_id=f.rule_id,
            rule_version=f.rule_version,
            object_id=f.object_id,
            severity=f.severity.value,
            title=f.title,
            description=f.description,
            evidence=[
                DiagnosticEvidenceResponse(
                    object_id=ev.object_id,
                    field_name=ev.field_name,
                    observed_value=ev.observed_value,
                    expected_value=ev.expected_value,
                    message=ev.message,
                    context_data=ev.context_data,
                )
                for ev in f.evidence
            ],
            severity_rationale=f.severity_rationale,
            recommendation=f.recommendation,
            category=(
                f.category.value
                if hasattr(f, "category") and hasattr(f.category, "value")
                else None
            ),
            classification=(
                f.classification.value
                if hasattr(f, "classification") and hasattr(f.classification, "value")
                else None
            ),
            original_severity=(
                f.original_severity.value
                if hasattr(f, "original_severity") and hasattr(f.original_severity, "value")
                else None
            ),
            confidence=(
                f.confidence.value
                if hasattr(f, "confidence") and hasattr(f.confidence, "value")
                else None
            ),
            metadata_completeness=(
                f.metadata_completeness.value
                if hasattr(f, "metadata_completeness") and hasattr(f.metadata_completeness, "value")
                else None
            ),
            structured_recommendation=(
                f.structured_recommendation.to_canonical_dict()
                if hasattr(f, "structured_recommendation") and f.structured_recommendation
                else None
            ),
            lifecycle_state=(
                f.lifecycle_state.value
                if hasattr(f, "lifecycle_state") and hasattr(f.lifecycle_state, "value")
                else None
            ),
            is_suppressed=getattr(f, "is_suppressed", False),
            suppression_id=getattr(f, "suppression_id", None),
            override_id=getattr(f, "override_id", None),
            priority_score=getattr(f, "priority_score", None),
            priority_rank=(
                f.priority_rank.value
                if hasattr(f, "priority_rank") and hasattr(f.priority_rank, "value")
                else None
            ),
            finding_id=getattr(f, "finding_id", None),
        )
        for f in report.findings
    ]

    evals_resp = [
        DiagnosticEvaluationResponse(
            rule_id=ev.rule_id,
            rule_version=ev.rule_version,
            status=ev.status.value,
            execution_duration_ms=ev.execution_duration_ms,
            message=ev.message,
            error_details=ev.error_details,
        )
        for ev in report.rule_evaluations
    ]

    return DiagnosticReportResponse(
        evaluation_id=report.evaluation_id,
        evaluated_at=report.evaluated_at,
        snapshot_id=report.snapshot_id,
        rule_set_version=report.rule_set_version,
        config_fingerprint=report.config_fingerprint,
        report_hash=report.report_hash,
        source_engine=report.source_engine,
        summary=report.summary.to_canonical_dict(),
        coverage=report.coverage.to_canonical_dict(),
        findings=findings_resp,
        rule_evaluations=evals_resp,
        explainability=(
            report.explainability.to_canonical_dict()
            if getattr(report, "explainability", None)
            else None
        ),
        severity_policy_version=getattr(report, "severity_policy_version", "1.0.0"),
        recommendation_catalog_version=getattr(report, "recommendation_catalog_version", "1.0.0"),
        suppressions_applied=list(getattr(report, "suppressions_applied", ())),
        severity_overrides_applied=list(getattr(report, "severity_overrides_applied", ())),
    )
