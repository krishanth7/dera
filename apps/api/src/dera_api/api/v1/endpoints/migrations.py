"""DERA API — Phase 9 Migration Engineering and Governance Endpoints.

Provides authenticated, tenant-isolated, deterministic APIs for:
- Listing and selecting immutable schema snapshots
- Comparing schema snapshots (Phase 9.1)
- Assessing migration risks and blast radius (Phase 9.2)
- Generating ordered migration plans (Phase 9.3)
- Compiling review-only dialect SQL artifacts (Phase 9.4)
- Governance review workflow, SoD enforcement, and approvals (Phase 9.5)
- Immutable cryptographic audit logs and authorized exports (Phase 9.5)
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from dera_api.api.v1.endpoints.migrations_auth import (
    MigrationAuthorizationContext,
    require_migration_auth,
)
from dera_api.api.v1.endpoints.migrations_service import MigrationService
from dera_api.api.v1.endpoints.reverse_engineering.deps import get_re_service
from dera_api.api.v1.endpoints.reverse_engineering.service import ReverseEngineeringService
from dera_api.auth.roles import Permission
from dera_api.contracts.errors import ProblemDetail
from dera_api.db.dependencies import get_db_session
from dera_api.schemas.migrations import (
    AuditEventResponse,
    GovernanceAuditResponse,
    GovernanceDecisionSubmitRequest,
    GovernanceReviewResponse,
    GovernanceReviewSubmitRequest,
    MigrationCompareRequest,
    MigrationExportResponse,
    MigrationPlanRequest,
    MigrationPlanResponse,
    MigrationRiskRequest,
    MigrationRiskResponse,
    MigrationSnapshotListResponse,
    MigrationSnapshotSummary,
    MigrationSqlArtifactResponse,
    MigrationSqlCompileRequest,
    PlanSummarySchema,
    RiskSummarySchema,
    SchemaComparisonResponse,
)

router = APIRouter(prefix="/migrations", tags=["Migration Engineering"])


def get_migration_service(
    request: Request,
    re_service: Annotated[ReverseEngineeringService, Depends(get_re_service)],
) -> MigrationService:
    """Retrieve or initialize migration service singleton on application state."""
    if hasattr(request, "app") and hasattr(request.app, "state"):
        if not hasattr(request.app.state, "migration_service"):
            request.app.state.migration_service = MigrationService(re_service=re_service)
        return request.app.state.migration_service
    return MigrationService(re_service=re_service)


# --- 1. Snapshots ---


@router.get(
    "/snapshots",
    response_model=MigrationSnapshotListResponse,
    summary="List immutable schema snapshots for migration comparison",
    responses={
        200: {"model": MigrationSnapshotListResponse, "description": "Snapshots retrieved."},
        400: {"model": ProblemDetail, "description": "Invalid workspace context."},
        401: {"model": ProblemDetail, "description": "Authentication required."},
        403: {"model": ProblemDetail, "description": "Forbidden / Access denied."},
    },
)
async def list_migration_snapshots(
    auth_ctx: Annotated[
        MigrationAuthorizationContext,
        Depends(require_migration_auth(Permission.MIGRATION_READ)),
    ],
    service: Annotated[MigrationService, Depends(get_migration_service)],
) -> MigrationSnapshotListResponse:
    """Retrieve all immutable snapshots available within the authorized workspace."""
    workspace_id = str(auth_ctx.workspace_id)
    snapshots = await service.list_snapshots(workspace_id=workspace_id)
    summaries = [
        MigrationSnapshotSummary(
            id=s.snapshot_id,
            name=s.payload.database_name or str(s.envelope.database_id),
            database_id=str(s.envelope.database_id),
            database_name=s.payload.database_name,
            engine=s.payload.engine,
            engine_version=s.payload.engine_version or "unknown",
            captured_at=s.envelope.capture_timestamp,
            fingerprint=s.fingerprint,
            table_count=len(s.payload.tables),
            view_count=len(s.payload.views),
            tags=[f"{k}:{v}" for k, v in s.envelope.tags.items()],
        )
        for s in snapshots
    ]
    return MigrationSnapshotListResponse(snapshots=summaries, total_count=len(summaries))


# --- 2. Compare (Phase 9.1) ---


@router.post(
    "/compare",
    response_model=SchemaComparisonResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute deterministic schema comparison between two snapshots",
    responses={
        200: {"model": SchemaComparisonResponse, "description": "Comparison completed."},
        400: {"model": ProblemDetail, "description": "Invalid request or incompatible snapshots."},
        401: {"model": ProblemDetail, "description": "Authentication required."},
        403: {"model": ProblemDetail, "description": "Forbidden / Access denied."},
    },
)
async def compare_snapshots(
    payload: MigrationCompareRequest,
    auth_ctx: Annotated[
        MigrationAuthorizationContext,
        Depends(require_migration_auth(Permission.MIGRATION_COMPARE)),
    ],
    service: Annotated[MigrationService, Depends(get_migration_service)],
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
) -> SchemaComparisonResponse:
    """Compare baseline and target schema snapshots deterministically."""
    workspace_id = str(auth_ctx.workspace_id)
    try:
        report = await service.compare_snapshots(
            workspace_id=workspace_id,
            baseline_snapshot_id=payload.baseline_snapshot_id,
            target_snapshot_id=payload.target_snapshot_id,
            db_session=db_session,
        )
        await db_session.commit()
    except ValueError as e:
        await db_session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception:
        await db_session.rollback()
        raise

    summary_data = {
        "total_changes": report.summary.total_changes,
        "total_added": report.summary.total_added,
        "total_removed": report.summary.total_removed,
        "total_modified": report.summary.total_modified,
        "tables_affected": report.summary.changes_by_object_type.get("TABLE", 0)
        if hasattr(report.summary, "changes_by_object_type")
        else 0,
    }

    # Normalize changes for response serialization
    changes = [c.model_dump(mode="json") for c in report.changes]

    return SchemaComparisonResponse(
        comparison_id=report.report_id,
        baseline_snapshot_id=report.baseline_snapshot_id,
        target_snapshot_id=report.target_snapshot_id,
        engine=report.engine,
        compared_at=datetime.now(UTC),
        comparison_fingerprint=report.report_fingerprint,
        summary=summary_data,
        changes=changes,
    )


@router.get(
    "/compare/{comparison_id}",
    response_model=SchemaComparisonResponse,
    summary="Retrieve comparison report",
)
async def get_comparison(
    comparison_id: str,
    auth_ctx: Annotated[
        MigrationAuthorizationContext,
        Depends(require_migration_auth(Permission.MIGRATION_COMPARE)),
    ],
    service: Annotated[MigrationService, Depends(get_migration_service)],
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
) -> SchemaComparisonResponse:
    workspace_id = str(auth_ctx.workspace_id)
    report = await service.get_comparison(
        workspace_id=workspace_id, comparison_id=comparison_id, db_session=db_session
    )
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Comparison report not found."
        )

    return SchemaComparisonResponse(
        comparison_id=report.report_id,
        baseline_snapshot_id=report.baseline_snapshot_id,
        target_snapshot_id=report.target_snapshot_id,
        engine=report.engine,
        compared_at=datetime.now(UTC),
        comparison_fingerprint=report.report_fingerprint,
        summary={
            "total_changes": report.summary.total_changes,
            "total_added": report.summary.total_added,
            "total_removed": report.summary.total_removed,
            "total_modified": report.summary.total_modified,
            "tables_affected": report.summary.changes_by_object_type.get("TABLE", 0)
            if hasattr(report.summary, "changes_by_object_type")
            else 0,
        },
        changes=[c.model_dump(mode="json") for c in report.changes],
    )


# --- 3. Risk Assessment (Phase 9.2) ---


@router.post(
    "/risk-assessments",
    response_model=MigrationRiskResponse,
    summary="Assess migration risks from verified comparison",
)
async def assess_migration_risk(
    payload: MigrationRiskRequest,
    auth_ctx: Annotated[
        MigrationAuthorizationContext,
        Depends(require_migration_auth(Permission.MIGRATION_COMPARE)),
    ],
    service: Annotated[MigrationService, Depends(get_migration_service)],
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
) -> MigrationRiskResponse:
    workspace_id = str(auth_ctx.workspace_id)
    try:
        report = await service.assess_risk(
            workspace_id=workspace_id,
            comparison_id=payload.comparison_id,
            db_session=db_session,
        )
        await db_session.commit()
    except ValueError as e:
        await db_session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception:
        await db_session.rollback()
        raise

    return MigrationRiskResponse(
        report_id=report.report_id,
        comparison_id=report.comparison_report_id,
        generated_at=datetime.now(UTC),
        fingerprint=report.report_fingerprint,
        summary=RiskSummarySchema(
            critical_count=report.summary.risks_by_severity.get("CRITICAL", 0),
            high_count=report.summary.risks_by_severity.get("HIGH", 0),
            medium_count=report.summary.risks_by_severity.get("MEDIUM", 0),
            low_count=report.summary.risks_by_severity.get("LOW", 0),
            informational_count=report.summary.risks_by_severity.get("INFORMATIONAL", 0),
            breaking_change_count=report.summary.potentially_breaking,
            potentially_breaking=report.summary.potentially_breaking,
            safe_change_count=report.summary.additive_changes,
            overall_risk_level=(
                "CRITICAL"
                if report.summary.risks_by_severity.get("CRITICAL", 0) > 0
                else "HIGH"
                if (
                    report.summary.risks_by_severity.get("HIGH", 0) > 0
                    or report.summary.potentially_breaking > 0
                )
                else "MEDIUM"
                if report.summary.risks_by_severity.get("MEDIUM", 0) > 0
                else "LOW"
            ),
            overall_recommendation="REVIEW_REQUIRED"
            if (report.summary.requires_review > 0 or report.summary.potentially_breaking > 0)
            else "PROCEED",
        ),
        risks=[r.model_dump(mode="json") for r in report.risk_assessments],
        recommendations=[rec.model_dump(mode="json") for rec in report.recommendations],
    )


# --- 4. Migration Planning (Phase 9.3) ---


@router.post(
    "/plans",
    response_model=MigrationPlanResponse,
    summary="Generate dependency-ordered migration plan",
)
async def generate_migration_plan(
    payload: MigrationPlanRequest,
    auth_ctx: Annotated[
        MigrationAuthorizationContext,
        Depends(require_migration_auth(Permission.MIGRATION_PLAN)),
    ],
    service: Annotated[MigrationService, Depends(get_migration_service)],
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
) -> MigrationPlanResponse:
    workspace_id = str(auth_ctx.workspace_id)
    try:
        plan = await service.generate_plan(
            workspace_id=workspace_id,
            comparison_id=payload.comparison_id,
            db_session=db_session,
        )
        await db_session.commit()
    except ValueError as e:
        await db_session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception:
        await db_session.rollback()
        raise

    return MigrationPlanResponse(
        plan_id=plan.plan_id,
        comparison_id=payload.comparison_id,
        engine=plan.target_engine,
        plan_fingerprint=plan.plan_fingerprint,
        summary=PlanSummarySchema(
            total_operations=plan.summary.total_operations,
            total_stages=plan.summary.stages_count,
            estimated_duration_seconds=0.0,
            manual_decision_gates_count=plan.summary.manual_decision_gates_count,
            manual_gates_count=plan.summary.manual_decision_gates_count,
        ),
        stages=[s.model_dump(mode="json") for s in plan.stages],
        unsupported_operations=[],
    )


# --- 5. SQL Compiler (Phase 9.4) ---


@router.post(
    "/sql-artifacts",
    response_model=MigrationSqlArtifactResponse,
    summary="Compile review-only dialect SQL artifact",
)
async def compile_sql_artifact(
    payload: MigrationSqlCompileRequest,
    auth_ctx: Annotated[
        MigrationAuthorizationContext,
        Depends(require_migration_auth(Permission.MIGRATION_PLAN)),
    ],
    service: Annotated[MigrationService, Depends(get_migration_service)],
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
) -> MigrationSqlArtifactResponse:
    workspace_id = str(auth_ctx.workspace_id)
    try:
        artifact = await service.compile_sql_artifact(
            workspace_id=workspace_id,
            plan_id=payload.plan_id,
            target_dialect=payload.target_dialect,
            target_version=payload.target_version,
            db_session=db_session,
        )
        await db_session.commit()
    except ValueError as e:
        await db_session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception:
        await db_session.rollback()
        raise

    return MigrationSqlArtifactResponse(
        artifact_id=artifact.artifact_id,
        plan_id=artifact.source_plan_id,
        target_dialect=artifact.dialect.value
        if hasattr(artifact.dialect, "value")
        else str(artifact.dialect),
        target_version=artifact.target_engine or "default",
        compiled_at=datetime.now(UTC),
        artifact_fingerprint=artifact.artifact_fingerprint,
        forward_sql=artifact.rendered_sql_script,
        rollback_sql="\n\n".join(r.sql for r in artifact.rollback_statements),
        transactional=len(artifact.transaction_blocks) > 0,
        validation_status=artifact.status.value
        if hasattr(artifact.status, "value")
        else str(artifact.status),
        validation_errors=[v.message for v in artifact.validation_issues],
        disclaimer=artifact.execution_notice,
    )


# --- 6. Governance & Review Workflow (Phase 9.5) ---


@router.post(
    "/reviews",
    response_model=GovernanceReviewResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit compiled SQL artifact for governance review",
)
async def submit_governance_review(
    payload: GovernanceReviewSubmitRequest,
    auth_ctx: Annotated[
        MigrationAuthorizationContext,
        Depends(require_migration_auth(Permission.MIGRATION_REVIEW)),
    ],
    service: Annotated[MigrationService, Depends(get_migration_service)],
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
) -> GovernanceReviewResponse:
    workspace_id = str(auth_ctx.workspace_id)
    requester_id = str(auth_ctx.user_id)

    try:
        review = await service.submit_for_review(
            workspace_id=workspace_id,
            artifact_id=payload.artifact_id,
            requester_id=requester_id,
            title=payload.title,
            description=payload.description or "",
            db_session=db_session,
        )
        await db_session.commit()
    except ValueError as e:
        await db_session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception:
        await db_session.rollback()
        raise

    return GovernanceReviewResponse(
        review_id=review.review_id,
        artifact_id=review.artifact_id,
        artifact_fingerprint=review.artifact_fingerprint,
        requester_id=review.requester_id,
        status=review.status.value,
        title=payload.title,
        description=payload.description,
        created_at=review.created_at,
        updated_at=review.created_at,
        required_approvals=review.required_approvals
        if hasattr(review, "required_approvals")
        else 1,
        current_approvals=len([d for d in review.decisions if d.decision_type.value == "APPROVE"]),
        decisions=[d.model_dump(mode="json") for d in review.decisions],
    )


@router.get(
    "/reviews",
    response_model=list[GovernanceReviewResponse],
    summary="List all governance reviews for authorized workspace",
)
async def list_governance_reviews(
    auth_ctx: Annotated[
        MigrationAuthorizationContext,
        Depends(require_migration_auth(Permission.MIGRATION_READ)),
    ],
    service: Annotated[MigrationService, Depends(get_migration_service)],
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[GovernanceReviewResponse]:
    workspace_id = str(auth_ctx.workspace_id)
    reviews = await service.list_reviews(workspace_id=workspace_id, db_session=db_session)
    return [
        GovernanceReviewResponse(
            review_id=r.review_id,
            artifact_id=r.artifact_id,
            artifact_fingerprint=r.artifact_fingerprint,
            requester_id=r.requester_id,
            status=r.status.value,
            title="Migration Governance Review",
            description="",
            created_at=r.created_at,
            updated_at=r.created_at,
            required_approvals=1,
            current_approvals=len([d for d in r.decisions if d.decision_type.value == "APPROVE"]),
            decisions=[d.model_dump(mode="json") for d in r.decisions],
        )
        for r in reviews
    ]


@router.get(
    "/reviews/{review_id}",
    response_model=GovernanceReviewResponse,
    summary="Retrieve governance review request",
)
async def get_governance_review(
    review_id: str,
    auth_ctx: Annotated[
        MigrationAuthorizationContext,
        Depends(require_migration_auth(Permission.MIGRATION_READ)),
    ],
    service: Annotated[MigrationService, Depends(get_migration_service)],
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
) -> GovernanceReviewResponse:
    workspace_id = str(auth_ctx.workspace_id)
    review = await service.get_review(
        workspace_id=workspace_id,
        review_id=review_id,
        db_session=db_session,
    )
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Review request not found."
        )

    return GovernanceReviewResponse(
        review_id=review.review_id,
        artifact_id=review.artifact_id,
        artifact_fingerprint=review.artifact_fingerprint,
        requester_id=review.requester_id,
        status=review.status.value,
        title="Migration Governance Review",
        description="",
        created_at=review.created_at,
        updated_at=review.created_at,
        required_approvals=1,
        current_approvals=len([d for d in review.decisions if d.decision_type.value == "APPROVE"]),
        decisions=[d.model_dump(mode="json") for d in review.decisions],
    )


@router.post(
    "/reviews/{review_id}/decisions",
    response_model=GovernanceReviewResponse,
    summary="Record reviewer governance decision enforcing SoD and role authorization",
)
async def record_governance_decision(
    review_id: str,
    payload: GovernanceDecisionSubmitRequest,
    auth_ctx: Annotated[
        MigrationAuthorizationContext,
        Depends(require_migration_auth(Permission.MIGRATION_APPROVE)),
    ],
    service: Annotated[MigrationService, Depends(get_migration_service)],
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
) -> GovernanceReviewResponse:
    workspace_id = str(auth_ctx.workspace_id)
    reviewer_id = str(auth_ctx.user_id)
    effective_role = auth_ctx.role

    try:
        review = await service.record_decision(
            workspace_id=workspace_id,
            review_id=review_id,
            reviewer_id=reviewer_id,
            effective_role=effective_role,
            decision_type_str=payload.decision_type,
            rationale=payload.rationale,
            db_session=db_session,
        )
        await db_session.commit()
    except PermissionError as e:
        await db_session.rollback()
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e
    except ValueError as e:
        await db_session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception:
        await db_session.rollback()
        raise

    return GovernanceReviewResponse(
        review_id=review.review_id,
        artifact_id=review.artifact_id,
        artifact_fingerprint=review.artifact_fingerprint,
        requester_id=review.requester_id,
        status=review.status.value,
        title="Migration Governance Review",
        description="",
        created_at=review.created_at,
        updated_at=review.created_at,
        required_approvals=1,
        current_approvals=len([d for d in review.decisions if d.decision_type.value == "APPROVE"]),
        decisions=[d.model_dump(mode="json") for d in review.decisions],
    )


# --- 7. Audit Evidence & Export (Phase 9.5) ---


@router.get(
    "/reviews/{review_id}/audit",
    response_model=GovernanceAuditResponse,
    summary="Retrieve immutable audit trail for a governance review",
)
async def get_governance_audit(
    review_id: str,
    auth_ctx: Annotated[
        MigrationAuthorizationContext,
        Depends(require_migration_auth(Permission.MIGRATION_READ)),
    ],
    service: Annotated[MigrationService, Depends(get_migration_service)],
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
) -> GovernanceAuditResponse:
    workspace_id = str(auth_ctx.workspace_id)
    try:
        events = await service.get_audit_trail(
            workspace_id=workspace_id,
            review_id=review_id,
            db_session=db_session,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e

    audit_responses = [
        AuditEventResponse(
            event_id=e.event_id,
            review_id=e.review_id,
            event_type=e.event_type,
            actor_id=e.actor_id,
            actor_role="reviewer",
            timestamp=e.timestamp,
            payload_hash=e.event_hash,
            details={"previous_state": e.previous_state, "new_state": e.new_state},
        )
        for e in events
    ]
    return GovernanceAuditResponse(review_id=review_id, events=audit_responses)


@router.get(
    "/reviews/{review_id}/export",
    response_model=MigrationExportResponse,
    summary="Export approved migration SQL artifact ensuring fail-closed status",
)
async def export_approved_migration(
    review_id: str,
    auth_ctx: Annotated[
        MigrationAuthorizationContext,
        Depends(require_migration_auth(Permission.MIGRATION_EXPORT)),
    ],
    service: Annotated[MigrationService, Depends(get_migration_service)],
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
) -> MigrationExportResponse:
    workspace_id = str(auth_ctx.workspace_id)
    user_id = str(auth_ctx.user_id)
    user_role = auth_ctx.role

    try:
        export_pkg = await service.export_approved_artifact(
            workspace_id=workspace_id,
            review_id=review_id,
            user_id=user_id,
            user_role=user_role,
            db_session=db_session,
        )
        await db_session.commit()
    except PermissionError as e:
        await db_session.rollback()
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e
    except ValueError as e:
        await db_session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception:
        await db_session.rollback()
        raise

    return MigrationExportResponse(**export_pkg)
