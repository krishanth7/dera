"""Authenticated workspace-scoped offline SQL analysis. No connector dependencies."""

from typing import Annotated, Literal

from dera.sql_engineering import Analysis, analyze
from dera.sql_engineering.diagnostics import SqlDiagnosticsEngine, SqlDiagnosticsReport
from dera.sql_engineering.execution_plans import ExecutionPlan, PlanInputError, analyze_plan
from dera.sql_engineering.execution_plans.parser import check_depth
from dera.sql_engineering.models import Dialect
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.routing import APIRoute
from pydantic import BaseModel, ConfigDict, Field
from starlette.concurrency import run_in_threadpool

from dera_api.api.v1.endpoints.reverse_engineering.deps import get_re_service
from dera_api.api.v1.endpoints.reverse_engineering.service import ReverseEngineeringService
from dera_api.auth.dependencies import require_workspace_permission_by_id, verify_csrf
from dera_api.auth.policies import has_permission
from dera_api.auth.roles import Permission
from dera_api.contracts.errors import ProblemDetail


class BoundedRoute(APIRoute):
    """Bound the streamed JSON body before FastAPI decoding, including chunked requests."""

    max_body_bytes = 65_536

    def validate_body(self, body: bytes) -> None:
        """Optional pre-decoder validation hook for bounded analysis routes."""

    def get_route_handler(self):
        original = super().get_route_handler()

        async def bounded(request: Request):
            body = bytearray()
            async for chunk in request.stream():
                if len(body) + len(chunk) > self.max_body_bytes:
                    raise HTTPException(413, "Analysis request exceeds byte limit.")
                body.extend(chunk)
            await run_in_threadpool(self.validate_body, bytes(body))
            request._body = bytes(body)
            return await original(request)

        return bounded


router = APIRouter(prefix="/sql-engineering", tags=["SQL Engineering"], route_class=BoundedRoute)


class AnalyzeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    sql: str = Field(min_length=1, max_length=16_384)
    dialect: Dialect


@router.post(
    "/analyze",
    response_model=Analysis,
    dependencies=[Depends(verify_csrf)],
    responses={
        413: {"model": ProblemDetail, "description": "SQL analysis body exceeds byte limit"}
    },
)
def analyze_sql(
    body: AnalyzeRequest,
    authorization: Annotated[
        tuple, Depends(require_workspace_permission_by_id(Permission.SCHEMA_READ))
    ],
) -> Analysis:
    """Analyze SQL without execution; workspace_id query parameter is server-authorized."""
    return analyze(body.sql, body.dialect)


class DiagnosticsOptions(BaseModel):
    model_config = ConfigDict(extra="forbid")
    include_complexity: bool = True
    include_recommendations: bool = True


class DiagnosticsRequest(AnalyzeRequest):
    schema_snapshot_id: str | None = Field(default=None, min_length=1, max_length=200)
    options: DiagnosticsOptions = Field(default_factory=DiagnosticsOptions)


@router.post(
    "/diagnostics",
    response_model=SqlDiagnosticsReport,
    dependencies=[Depends(verify_csrf)],
    responses={
        413: {"model": ProblemDetail, "description": "SQL diagnostics request exceeds byte limit"}
    },
)
async def diagnose_sql(
    body: DiagnosticsRequest,
    authorization: Annotated[
        tuple, Depends(require_workspace_permission_by_id(Permission.SCHEMA_READ))
    ],
    service: Annotated[ReverseEngineeringService, Depends(get_re_service)],
) -> SqlDiagnosticsReport:
    """Static SQL diagnostics, using only an authorized immutable stored snapshot."""
    workspace, membership = authorization
    snapshot = None
    if body.schema_snapshot_id:
        if not has_permission(membership.role, Permission.SNAPSHOT_READ):
            raise HTTPException(403, "Snapshot read permission required.")
        snapshot = await service.get_snapshot(str(workspace.id), body.schema_snapshot_id)
        # Defense in depth even if a storage adapter incorrectly ignores workspace_id.
        if snapshot is None or snapshot.workspace_id != str(workspace.id):
            raise HTTPException(404, "Snapshot not found in authorized workspace.")
        snapshot = snapshot.model_copy(deep=True)
    try:
        return await run_in_threadpool(
            SqlDiagnosticsEngine().analyze,
            body.sql,
            body.dialect,
            snapshot,
            include_complexity=body.options.include_complexity,
            include_recommendations=body.options.include_recommendations,
        )
    except ValueError:
        raise HTTPException(
            422,
            "Snapshot is incompatible, exceeds analysis limits or fails integrity verification.",
        ) from None


# Plans are submitted as a JSON string so nesting can be checked before decoding.
class PlanBoundedRoute(BoundedRoute):
    max_body_bytes = 6_500_000

    def validate_body(self, body: bytes) -> None:
        try:
            check_depth(body.decode("utf-8"))
        except (PlanInputError, UnicodeError):
            raise HTTPException(422, "Invalid or over-limit analysis request envelope.") from None


class PlanAnalyzeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    dialect: Dialect
    format: Literal["postgresql-json", "mysql-json-v1", "mariadb-json", "sqlite-eqp"]
    plan_json: str = Field(min_length=1, max_length=1_048_576)
    sql: str | None = Field(default=None, max_length=16_384)


plan_router = APIRouter(route_class=PlanBoundedRoute)


@plan_router.post(
    "/execution-plans/analyze",
    response_model=ExecutionPlan,
    dependencies=[Depends(verify_csrf)],
    responses={
        413: {"model": ProblemDetail, "description": "Imported plan request exceeds byte limit"}
    },
)
async def analyze_execution_plan(
    body: PlanAnalyzeRequest,
    response: Response,
    authorization: Annotated[
        tuple, Depends(require_workspace_permission_by_id(Permission.SCHEMA_READ))
    ],
) -> ExecutionPlan:
    """Offline import only. No database identity, connection or live acquisition is accepted."""
    response.headers["Cache-Control"] = "no-store"
    try:
        return await run_in_threadpool(
            analyze_plan, body.plan_json, body.dialect, body.format, body.sql
        )
    except (PlanInputError, ValueError):
        raise HTTPException(
            422, "Invalid, unsupported or over-limit imported execution plan."
        ) from None


router.include_router(plan_router)
