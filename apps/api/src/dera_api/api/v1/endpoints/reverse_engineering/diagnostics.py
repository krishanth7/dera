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
        config = DiagnosticEngineConfig(
            enabled_rule_ids=enabled,
            disabled_rule_ids=disabled,
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
    )
