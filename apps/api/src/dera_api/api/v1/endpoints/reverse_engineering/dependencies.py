"""DERA API — Phase 6.6 Dependency Analysis Endpoints.

Provides execution ordering (creation/drop order, parallel migration levels)
and table-level dependency traversal.
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
    DependencyAnalysisResponse,
    TableDependencyResponse,
    TopologicalLevelResponse,
)

router = APIRouter()


@router.get(
    "/schemas/{schema_id}/dependencies",
    response_model=DependencyAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve complete schema dependency analysis",
    responses={
        200: {"model": DependencyAnalysisResponse, "description": "Dependency analysis retrieved."},
        401: {"model": ProblemDetail, "description": "Authentication required."},
        403: {"model": ProblemDetail, "description": "Forbidden / Access denied."},
        404: {"model": ProblemDetail, "description": "Schema not found in authorized workspace."},
    },
)
async def get_schema_dependencies(
    schema_id: str,
    workspace_id: Annotated[str, Depends(resolve_authorized_workspace_id)],
    service: Annotated[ReverseEngineeringService, Depends(get_re_service)],
) -> DependencyAnalysisResponse:
    """Return validated dependency analysis including creation order, drop order, and parallel levels."""
    dep_res = service.get_dependency_analysis(workspace_id, schema_id)
    if not dep_res:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Schema with ID '{schema_id}' was not found in authorized workspace.",
        )

    levels_resp = [
        TopologicalLevelResponse(
            level_index=lvl.level_index,
            table_ids=list(lvl.table_ids),
        )
        for lvl in dep_res.ordering.levels
    ]

    return DependencyAnalysisResponse(
        database_name=dep_res.database_name,
        total_tables=dep_res.node_count,
        total_edges=dep_res.edge_count,
        has_cycles=dep_res.cycle_report.has_cycles,
        cycle_count=dep_res.cycle_report.cycle_count,
        scc_count=dep_res.cycle_report.scc_count,
        cyclic_scc_count=dep_res.cycle_report.cyclic_scc_count,
        creation_order=list(dep_res.ordering.creation_order),
        drop_order=list(dep_res.ordering.drop_order),
        levels=levels_resp,
    )


@router.get(
    "/schemas/{schema_id}/tables/{table_id}/dependencies",
    response_model=TableDependencyResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve dependencies for a specific table",
    responses={
        200: {"model": TableDependencyResponse, "description": "Table dependencies retrieved."},
        401: {"model": ProblemDetail, "description": "Authentication required."},
        403: {"model": ProblemDetail, "description": "Forbidden / Access denied."},
        404: {
            "model": ProblemDetail,
            "description": "Schema or table not found in authorized workspace.",
        },
    },
)
async def get_table_dependencies(
    schema_id: str,
    table_id: str,
    workspace_id: Annotated[str, Depends(resolve_authorized_workspace_id)],
    service: Annotated[ReverseEngineeringService, Depends(get_re_service)],
) -> TableDependencyResponse:
    """Return incoming dependencies, dependents, and cycle classification for a given table."""
    dep_res = service.get_dependency_analysis(workspace_id, schema_id)
    if not dep_res:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Schema with ID '{schema_id}' was not found in authorized workspace.",
        )

    graph = service.get_relationship_graph(workspace_id, schema_id)
    if not graph or table_id not in graph.nodes:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Table with ID '{table_id}' was not found in schema.",
        )

    # In dependency analysis: child depends on parent.
    # Therefore, table's dependencies are tables it references (outgoing edges in FK graph: child -> parent).
    # Table's dependents are tables that reference it (incoming edges in FK graph: child -> this table).
    direct_dependencies = sorted(
        {
            getattr(e, "referenced_table_id", getattr(e, "target_table_id", ""))
            for e in graph.edges
            if e.source_table_id == table_id
        }
    )
    direct_dependents = sorted(
        {
            e.source_table_id
            for e in graph.edges
            if getattr(e, "referenced_table_id", getattr(e, "target_table_id", "")) == table_id
        }
    )

    # Cycle check
    in_cycle = False
    scc_id = None
    for scc in dep_res.cycle_report.components:
        if table_id in scc.table_ids:
            in_cycle = scc.is_cyclic
            scc_id = scc.scc_id
            break

    return TableDependencyResponse(
        table_id=table_id,
        direct_dependencies=direct_dependencies,
        direct_dependents=direct_dependents,
        in_cycle=in_cycle,
        scc_id=scc_id,
    )
