"""DERA API — Phase 6.6 Cycle Detection Report Endpoints.

Provides inspection of cyclic dependencies, strongly connected components,
and cycle resolution strategies.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from dera_api.api.v1.endpoints.reverse_engineering.deps import (
    get_re_service,
    resolve_authorized_workspace_id,
)
from dera_api.api.v1.endpoints.reverse_engineering.service import ReverseEngineeringService
from dera_api.contracts.errors import ProblemDetail
from dera_api.schemas.reverse_engineering import (
    CycleInstanceResponse,
    CycleReportResponse,
    SCCResponse,
)

router = APIRouter()


@router.get(
    "/schemas/{schema_id}/cycles",
    response_model=CycleReportResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve cycle detection report for a schema",
    responses={
        200: {"model": CycleReportResponse, "description": "Cycle report retrieved."},
        401: {"model": ProblemDetail, "description": "Authentication required."},
        403: {"model": ProblemDetail, "description": "Forbidden / Access denied."},
        404: {"model": ProblemDetail, "description": "Schema not found in authorized workspace."},
    },
)
async def get_schema_cycles(
    schema_id: str,
    workspace_id: Annotated[str, Depends(resolve_authorized_workspace_id)],
    service: Annotated[ReverseEngineeringService, Depends(get_re_service)],
) -> CycleReportResponse:
    """Return deterministic cycle detection report including elementary cycles and SCCs."""
    dep_res = service.get_dependency_analysis(workspace_id, schema_id)
    if not dep_res:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Schema with ID '{schema_id}' was not found in authorized workspace.",
        )

    cr = dep_res.cycle_report
    cycles_resp = [
        CycleInstanceResponse(
            cycle_id=c.cycle_id,
            cycle_kind=c.cycle_kind.value,
            table_ids=list(c.table_ids),
            length=len(c.table_ids),
            breakability_strategy=c.breakability.strategy.value if c.breakability else None,
        )
        for c in cr.cycles
    ]

    components_resp = [
        SCCResponse(
            scc_id=scc.scc_id,
            is_cyclic=scc.is_cyclic,
            table_ids=list(scc.table_ids),
            size=len(scc.table_ids),
        )
        for scc in cr.components
    ]

    return CycleReportResponse(
        has_cycles=cr.has_cycles,
        cycle_count=cr.cycle_count,
        scc_count=cr.scc_count,
        cyclic_scc_count=cr.cyclic_scc_count,
        cycles=cycles_resp,
        components=components_resp,
    )
