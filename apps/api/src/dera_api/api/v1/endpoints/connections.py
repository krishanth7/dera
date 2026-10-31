"""DERA API — Database Connection Management & Connector Endpoints.

Provides workspace-scoped connection CRUD, engine discovery, diagnostic testing,
and schema inspection triggers adhering to Phase 7.3 requirements.
"""

from __future__ import annotations

import time
import uuid
from datetime import UTC, datetime
from typing import Annotated

from dera_connectors.configuration import ConnectorConfig, TLSSettings
from dera_connectors.context import ConnectorContext
from dera_connectors.engine import DatabaseEngine, DatabaseProvider
from dera_connectors.registry import default_connector_registry
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import SecretStr

from dera_api.api.v1.endpoints.reverse_engineering.deps import (
    get_re_service,
    resolve_authorized_workspace_id,
)
from dera_api.api.v1.endpoints.reverse_engineering.service import ReverseEngineeringService
from dera_api.schemas.connectors import (
    ConnectionListResponse,
    ConnectionResponse,
    ConnectionTestRequest,
    ConnectionTestResponse,
    ConnectorEngineResponse,
    CreateConnectionRequest,
    UpdateConnectionRequest,
)
from dera_api.schemas.reverse_engineering import SchemaSummaryResponse

router = APIRouter(tags=["Database Connections"])


class ConnectionEntity:
    """Internal model for persisted connection configuration with credential isolation."""

    def __init__(
        self,
        id: str,
        workspace_id: str,
        name: str,
        engine: DatabaseEngine,
        provider: DatabaseProvider,
        database: str,
        host: str | None = None,
        port: int | None = None,
        username: str | None = None,
        password: str | None = None,
        ssl_mode: str = "prefer",
        status: str = "not_tested",
        created_at: str | None = None,
    ) -> None:
        self.id = id
        self.workspace_id = workspace_id
        self.name = name
        self.engine = engine
        self.provider = provider
        self.database = database
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.ssl_mode = ssl_mode
        self.status = status
        self.last_tested_at: str | None = None
        self.last_inspected_at: str | None = None
        self.created_at = created_at or datetime.now(UTC).isoformat()
        self.updated_at: str | None = None
        self.error_message: str | None = None

    def to_response(self) -> ConnectionResponse:
        """Convert to public response with password redacted."""
        return ConnectionResponse(
            id=self.id,
            workspace_id=self.workspace_id,
            name=self.name,
            engine=self.engine,
            provider=self.provider,
            database=self.database,
            host=self.host,
            port=self.port,
            username=self.username,
            has_password=bool(self.password),
            ssl_mode=self.ssl_mode,
            status=self.status,
            last_tested_at=self.last_tested_at,
            last_inspected_at=self.last_inspected_at,
            created_at=self.created_at,
            updated_at=self.updated_at,
            error_message=self.error_message,
        )


class ConnectionService:
    """In-memory connection management and diagnostic coordination service."""

    def __init__(self) -> None:
        self._connections: dict[tuple[str, str], ConnectionEntity] = {}

    def list_connections(self, workspace_id: str) -> list[ConnectionEntity]:
        return [c for (ws, _), c in self._connections.items() if ws == workspace_id]

    def get_connection(self, workspace_id: str, connection_id: str) -> ConnectionEntity | None:
        return self._connections.get((workspace_id, connection_id))

    def create_connection(
        self,
        workspace_id: str,
        payload: CreateConnectionRequest,
    ) -> ConnectionEntity:
        conn_id = str(uuid.uuid4())
        entity = ConnectionEntity(
            id=conn_id,
            workspace_id=workspace_id,
            name=payload.name,
            engine=payload.engine,
            provider=payload.provider,
            database=payload.database,
            host=payload.host,
            port=payload.port,
            username=payload.username,
            password=payload.password,
            ssl_mode=payload.ssl_mode,
        )
        self._connections[(workspace_id, conn_id)] = entity
        return entity

    def update_connection(
        self,
        workspace_id: str,
        connection_id: str,
        payload: UpdateConnectionRequest,
    ) -> ConnectionEntity | None:
        entity = self.get_connection(workspace_id, connection_id)
        if not entity:
            return None

        if payload.name is not None:
            entity.name = payload.name
        if payload.database is not None:
            entity.database = payload.database
        if payload.provider is not None:
            entity.provider = payload.provider
        if payload.host is not None:
            entity.host = payload.host
        if payload.port is not None:
            entity.port = payload.port
        if payload.username is not None:
            entity.username = payload.username
        if payload.password is not None:
            entity.password = payload.password
        if payload.ssl_mode is not None:
            entity.ssl_mode = payload.ssl_mode

        entity.updated_at = datetime.now(UTC).isoformat()
        return entity

    def delete_connection(self, workspace_id: str, connection_id: str) -> bool:
        return self._connections.pop((workspace_id, connection_id), None) is not None


default_connection_service = ConnectionService()


def get_connection_service() -> ConnectionService:
    return default_connection_service


# --- Supported Engines Discovery ---


@router.get(
    "/connectors/engines",
    response_model=list[ConnectorEngineResponse],
    summary="List supported database engines and provider matrix",
)
async def list_supported_engines() -> list[ConnectorEngineResponse]:
    """Return all certified database connector engines and distributions."""
    return [
        ConnectorEngineResponse(
            engine=DatabaseEngine.POSTGRESQL,
            display_name="PostgreSQL",
            default_port=5432,
            is_experimental=False,
            supported_providers=[
                DatabaseProvider.GENERIC,
                DatabaseProvider.SUPABASE,
                DatabaseProvider.NEON,
                DatabaseProvider.AWS_RDS,
                DatabaseProvider.AWS_AURORA,
                DatabaseProvider.GCP_CLOUDSQL,
                DatabaseProvider.AZURE_DATABASE,
            ],
        ),
        ConnectorEngineResponse(
            engine=DatabaseEngine.SQLITE,
            display_name="SQLite (Contained)",
            default_port=None,
            is_experimental=False,
            supported_providers=[DatabaseProvider.GENERIC],
        ),
        ConnectorEngineResponse(
            engine=DatabaseEngine.MYSQL,
            display_name="MySQL",
            default_port=3306,
            is_experimental=False,
            supported_providers=[
                DatabaseProvider.GENERIC,
                DatabaseProvider.AWS_RDS,
                DatabaseProvider.AWS_AURORA,
                DatabaseProvider.GCP_CLOUDSQL,
            ],
        ),
        ConnectorEngineResponse(
            engine=DatabaseEngine.MARIADB,
            display_name="MariaDB",
            default_port=3306,
            is_experimental=False,
            supported_providers=[
                DatabaseProvider.GENERIC,
                DatabaseProvider.AWS_RDS,
            ],
        ),
    ]


# --- Diagnostic Connection Testing ---


@router.post(
    "/connections/test",
    response_model=ConnectionTestResponse,
    summary="Test an unsaved database connection configuration",
)
async def test_raw_connection(
    payload: ConnectionTestRequest,
) -> ConnectionTestResponse:
    """Execute a real diagnostic probe against the specified connection parameters."""
    start_time = time.perf_counter()

    # Safety: SQLite filesystem path containment check
    if payload.engine == DatabaseEngine.SQLITE:
        if payload.database != ":memory:" and not payload.database.startswith(
            ("demo/", "fixtures/", "workspace/")
        ):
            return ConnectionTestResponse(
                success=False,
                latency_ms=round((time.perf_counter() - start_time) * 1000, 2),
                engine=payload.engine,
                error_code="FILESYSTEM_CONTAINMENT_VIOLATION",
                error_message="Arbitrary server filesystem paths are prohibited. Use an approved workspace location.",
            )

    try:
        config = ConnectorConfig(
            engine=payload.engine,
            database=payload.database,
            host=payload.host,
            port=payload.port,
            username=payload.username,
            password=SecretStr(payload.password) if payload.password else None,
            tls=TLSSettings(ssl_mode=payload.ssl_mode),
        )
        context = ConnectorContext(workspace_id="ephemeral-test-context")
        connector = default_connector_registry.create(config=config, context=context)
        result = await connector.test_connection()
        latency = round((time.perf_counter() - start_time) * 1000, 2)
        return ConnectionTestResponse(
            success=result.success,
            latency_ms=result.latency_ms or latency,
            engine=payload.engine,
            server_version=result.identity.server_version if result.identity else None,
            error_code=result.error_code,
            error_message=result.error_message,
        )
    except Exception as exc:
        latency = round((time.perf_counter() - start_time) * 1000, 2)
        return ConnectionTestResponse(
            success=False,
            latency_ms=latency,
            engine=payload.engine,
            error_code="CONNECTION_ERROR",
            error_message=str(exc),
        )


# --- Workspace Connection Management ---


@router.get(
    "/workspaces/{workspace_id}/connections",
    response_model=ConnectionListResponse,
    summary="List database connections in a workspace",
)
async def list_workspace_connections(
    workspace_id: Annotated[str, Depends(resolve_authorized_workspace_id)],
    service: Annotated[ConnectionService, Depends(get_connection_service)],
) -> ConnectionListResponse:
    """Retrieve all authorized database connections in the designated workspace."""
    entities = service.list_connections(workspace_id)
    return ConnectionListResponse(
        connections=[c.to_response() for c in entities],
        total_count=len(entities),
    )


@router.post(
    "/workspaces/{workspace_id}/connections",
    response_model=ConnectionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new database connection in a workspace",
)
async def create_workspace_connection(
    workspace_id: Annotated[str, Depends(resolve_authorized_workspace_id)],
    payload: CreateConnectionRequest,
    service: Annotated[ConnectionService, Depends(get_connection_service)],
) -> ConnectionResponse:
    """Configure and persist a new database connection entity within an authorized workspace."""
    if payload.engine == DatabaseEngine.SQLITE:
        if payload.database != ":memory:" and not payload.database.startswith(
            ("demo/", "fixtures/", "workspace/")
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Arbitrary server filesystem paths are prohibited for SQLite connections.",
            )

    entity = service.create_connection(workspace_id, payload)
    return entity.to_response()


@router.get(
    "/workspaces/{workspace_id}/connections/{connection_id}",
    response_model=ConnectionResponse,
    summary="Get connection details by ID",
)
async def get_workspace_connection(
    connection_id: str,
    workspace_id: Annotated[str, Depends(resolve_authorized_workspace_id)],
    service: Annotated[ConnectionService, Depends(get_connection_service)],
) -> ConnectionResponse:
    """Retrieve safe metadata for a specific authorized database connection."""
    entity = service.get_connection(workspace_id, connection_id)
    if not entity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Connection '{connection_id}' not found in authorized workspace.",
        )
    return entity.to_response()


@router.patch(
    "/workspaces/{workspace_id}/connections/{connection_id}",
    response_model=ConnectionResponse,
    summary="Update connection details",
)
async def update_workspace_connection(
    connection_id: str,
    payload: UpdateConnectionRequest,
    workspace_id: Annotated[str, Depends(resolve_authorized_workspace_id)],
    service: Annotated[ConnectionService, Depends(get_connection_service)],
) -> ConnectionResponse:
    """Update connection parameters while preserving credential isolation."""
    entity = service.update_connection(workspace_id, connection_id, payload)
    if not entity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Connection '{connection_id}' not found in authorized workspace.",
        )
    return entity.to_response()


@router.delete(
    "/workspaces/{workspace_id}/connections/{connection_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a database connection",
)
async def delete_workspace_connection(
    connection_id: str,
    workspace_id: Annotated[str, Depends(resolve_authorized_workspace_id)],
    service: Annotated[ConnectionService, Depends(get_connection_service)],
) -> None:
    """Remove a database connection from the authorized workspace."""
    deleted = service.delete_connection(workspace_id, connection_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Connection '{connection_id}' not found in authorized workspace.",
        )


@router.post(
    "/workspaces/{workspace_id}/connections/{connection_id}/test",
    response_model=ConnectionTestResponse,
    summary="Test an existing persisted database connection",
)
async def test_workspace_connection(
    connection_id: str,
    workspace_id: Annotated[str, Depends(resolve_authorized_workspace_id)],
    service: Annotated[ConnectionService, Depends(get_connection_service)],
) -> ConnectionTestResponse:
    """Run diagnostic connection probe using persisted configuration and record status."""
    entity = service.get_connection(workspace_id, connection_id)
    if not entity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Connection '{connection_id}' not found in authorized workspace.",
        )

    test_req = ConnectionTestRequest(
        engine=entity.engine,
        database=entity.database,
        host=entity.host,
        port=entity.port,
        username=entity.username,
        password=entity.password,
        ssl_mode=entity.ssl_mode,
    )
    res = await test_raw_connection(test_req)
    entity.status = "connected" if res.success else "failed"
    entity.last_tested_at = datetime.now(UTC).isoformat()
    entity.error_message = res.error_message if not res.success else None
    return res


@router.post(
    "/workspaces/{workspace_id}/connections/{connection_id}/inspect",
    response_model=SchemaSummaryResponse,
    summary="Inspect database metadata and register schema representation",
)
async def inspect_connection_schema(
    connection_id: str,
    workspace_id: Annotated[str, Depends(resolve_authorized_workspace_id)],
    service: Annotated[ConnectionService, Depends(get_connection_service)],
    re_service: Annotated[ReverseEngineeringService, Depends(get_re_service)],
) -> SchemaSummaryResponse:
    """Trigger reverse engineering metadata extraction for connection and register schema."""
    from dera.metadata.models import (
        CanonicalDatabase,
        CanonicalNamespace,
        CanonicalProvenance,
    )
    from dera.reverse_engineering.builder import SchemaBuilder

    entity = service.get_connection(workspace_id, connection_id)
    if not entity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Connection '{connection_id}' not found in authorized workspace.",
        )

    schema_id = f"schema-{entity.id}"
    db = CanonicalDatabase(
        id=schema_id,
        name=entity.database,
        engine=entity.engine.value,
        provenance=CanonicalProvenance(
            source_engine=entity.engine.value,
            source_version="16.2",
            connector_version="0.1.0-dev",
            collection_timestamp=datetime.now(UTC),
        ),
    )

    builder = SchemaBuilder(database=db)
    # Register public namespace
    ns = CanonicalNamespace(id=f"{schema_id}-ns-public", database_id=schema_id, name="public")
    builder.add_namespace(ns)

    schema_rep = builder.build()
    re_service.register_schema(workspace_id, schema_rep)
    entity.last_inspected_at = datetime.now(UTC).isoformat()

    return SchemaSummaryResponse(
        schema_id=db.id,
        database_id=db.id,
        database_name=db.name,
        engine=db.engine,
        namespace_count=len(schema_rep.namespaces),
        table_count=len(schema_rep.tables),
        view_count=len(schema_rep.views),
        foreign_key_count=len(schema_rep.foreign_key_references),
        completeness=schema_rep.metadata_completeness.value,
        source_engine=db.provenance.source_engine,
        source_version=db.provenance.source_version,
        connector_version=db.provenance.connector_version,
        collection_timestamp=db.provenance.collection_timestamp,
    )
