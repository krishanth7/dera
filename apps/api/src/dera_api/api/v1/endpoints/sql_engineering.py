"""Authenticated workspace-scoped offline SQL analysis. No connector dependencies."""

from typing import Annotated

from dera.sql_engineering import Analysis, analyze
from dera.sql_engineering.models import Dialect
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.routing import APIRoute
from pydantic import BaseModel, ConfigDict, Field

from dera_api.auth.dependencies import require_workspace_permission_by_id, verify_csrf
from dera_api.auth.roles import Permission
from dera_api.contracts.errors import ProblemDetail


class BoundedRoute(APIRoute):
    """Bound the streamed JSON body before FastAPI decoding, including chunked requests."""

    def get_route_handler(self):
        original = super().get_route_handler()

        async def bounded(request: Request):
            body = bytearray()
            async for chunk in request.stream():
                if len(body) + len(chunk) > 65_536:
                    raise HTTPException(413, "SQL analysis request exceeds 65536 bytes.")
                body.extend(chunk)
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
