"""DERA API — Phase 6.6 Relationship Graph Endpoints.

Provides directed multigraph traversal, composite edge inspection, and table relationship queries.
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
    RelationshipEdgeResponse,
    RelationshipGraphResponse,
    TableNodeResponse,
    TableRelationshipsResponse,
)

router = APIRouter()


@router.get(
    "/schemas/{schema_id}/relationships",
    response_model=RelationshipGraphResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve complete foreign key relationship graph",
    responses={
        200: {"model": RelationshipGraphResponse, "description": "Relationship graph retrieved."},
        401: {"model": ProblemDetail, "description": "Authentication required."},
        403: {"model": ProblemDetail, "description": "Forbidden / Access denied."},
        404: {"model": ProblemDetail, "description": "Schema not found in authorized workspace."},
    },
)
async def get_schema_relationships(
    schema_id: str,
    workspace_id: Annotated[str, Depends(resolve_authorized_workspace_id)],
    service: Annotated[ReverseEngineeringService, Depends(get_re_service)],
) -> RelationshipGraphResponse:
    """Return verified relationship graph nodes and directed foreign key edges."""
    graph = service.get_relationship_graph(workspace_id, schema_id)
    if not graph:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Schema with ID '{schema_id}' was not found in authorized workspace.",
        )

    nodes_resp = [
        TableNodeResponse(
            table_id=n.table_id,
            namespace=n.namespace,
            name=n.name,
        )
        for n in sorted(graph.nodes.values(), key=lambda n: (n.namespace, n.name, n.table_id))
    ]

    edges_resp = [
        RelationshipEdgeResponse(
            edge_id=e.edge_id,
            source_table_id=e.source_table_id,
            source_table_name=e.source_table_name,
            target_table_id=getattr(e, "referenced_table_id", getattr(e, "target_table_id", "")),
            target_table_name=getattr(
                e, "referenced_table_name", getattr(e, "target_table_name", "")
            ),
            constraint_name=e.native_name,
            source_columns=list(
                getattr(e, "source_column_names", getattr(e, "source_columns", ()))
            ),
            target_columns=list(
                getattr(e, "referenced_column_names", getattr(e, "target_columns", ()))
            ),
            on_delete=str(e.on_delete) if e.on_delete else None,
            on_update=str(e.on_update) if e.on_update else None,
        )
        for e in sorted(
            graph.edges,
            key=lambda e: (e.source_table_id, getattr(e, "referenced_table_id", ""), e.native_name),
        )
    ]

    return RelationshipGraphResponse(
        database_name=graph.database_name,
        engine=graph.engine,
        node_count=len(nodes_resp),
        edge_count=len(edges_resp),
        nodes=nodes_resp,
        edges=edges_resp,
    )


@router.get(
    "/schemas/{schema_id}/tables/{table_id}/relationships",
    response_model=TableRelationshipsResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve relationships for a specific table",
    responses={
        200: {"model": TableRelationshipsResponse, "description": "Table relationships retrieved."},
        401: {"model": ProblemDetail, "description": "Authentication required."},
        403: {"model": ProblemDetail, "description": "Forbidden / Access denied."},
        404: {
            "model": ProblemDetail,
            "description": "Schema or table not found in authorized workspace.",
        },
    },
)
async def get_table_relationships(
    schema_id: str,
    table_id: str,
    workspace_id: Annotated[str, Depends(resolve_authorized_workspace_id)],
    service: Annotated[ReverseEngineeringService, Depends(get_re_service)],
) -> TableRelationshipsResponse:
    """Return incoming and outgoing foreign key edges for a given table node."""
    graph = service.get_relationship_graph(workspace_id, schema_id)
    if not graph:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Schema with ID '{schema_id}' was not found in authorized workspace.",
        )

    if table_id not in graph.nodes:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Table with ID '{table_id}' was not found in relationship graph.",
        )

    incoming_resp: list[RelationshipEdgeResponse] = []
    outgoing_resp: list[RelationshipEdgeResponse] = []

    for edge in graph.edges:
        ref_tid = getattr(edge, "referenced_table_id", getattr(edge, "target_table_id", ""))
        edge_dto = RelationshipEdgeResponse(
            edge_id=edge.edge_id,
            source_table_id=edge.source_table_id,
            source_table_name=edge.source_table_name,
            target_table_id=ref_tid,
            target_table_name=getattr(
                edge, "referenced_table_name", getattr(edge, "target_table_name", "")
            ),
            constraint_name=edge.native_name,
            source_columns=list(
                getattr(edge, "source_column_names", getattr(edge, "source_columns", ()))
            ),
            target_columns=list(
                getattr(edge, "referenced_column_names", getattr(edge, "target_columns", ()))
            ),
            on_delete=str(edge.on_delete) if edge.on_delete else None,
            on_update=str(edge.on_update) if edge.on_update else None,
        )

        if edge.source_table_id == table_id:
            outgoing_resp.append(edge_dto)
        if ref_tid == table_id:
            incoming_resp.append(edge_dto)

    return TableRelationshipsResponse(
        table_id=table_id,
        incoming=sorted(incoming_resp, key=lambda e: (e.source_table_id, e.constraint_name)),
        outgoing=sorted(outgoing_resp, key=lambda e: (e.target_table_id, e.constraint_name)),
    )
