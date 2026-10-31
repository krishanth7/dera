"""DERA API — Connector Schemas & API Integration Contracts.

Defines Pydantic v2 schemas for connector engine discovery, capability matrices,
connection tests, and metadata inspection payloads.
"""

import uuid

from dera_connectors.capabilities import CapabilityStatus, ConnectorCapability
from dera_connectors.engine import DatabaseEngine, DatabaseProvider
from pydantic import BaseModel, ConfigDict, Field


class ConnectorEngineResponse(BaseModel):
    """Supported database connector engine descriptor."""

    model_config = ConfigDict(frozen=True)

    engine: DatabaseEngine = Field(..., description="Canonical engine identifier.")
    display_name: str = Field(..., description="Human-readable engine name.")
    default_port: int | None = Field(default=None, description="Default network port.")
    is_experimental: bool = Field(
        default=False, description="Whether engine support is experimental."
    )
    supported_providers: list[DatabaseProvider] = Field(
        default_factory=list,
        description="Supported cloud providers or platform distributions.",
    )


class CapabilityStatusResponse(BaseModel):
    """Capability availability detail."""

    model_config = ConfigDict(frozen=True)

    capability: ConnectorCapability
    status: CapabilityStatus
    reason: str | None = None


class ConnectorCapabilitiesResponse(BaseModel):
    """Collection of capabilities supported by a database connector."""

    model_config = ConfigDict(frozen=True)

    engine: DatabaseEngine
    capabilities: list[CapabilityStatusResponse] = Field(default_factory=list)


class ConnectionTestRequest(BaseModel):
    """Request payload to trigger a diagnostic connection test for a database."""

    model_config = ConfigDict(frozen=True)

    engine: DatabaseEngine
    database: str
    host: str | None = None
    port: int | None = None
    username: str | None = None
    password: str | None = None
    ssl_mode: str = "prefer"


class ConnectionTestResponse(BaseModel):
    """Response returned from a connection diagnostic probe."""

    model_config = ConfigDict(frozen=True)

    success: bool
    latency_ms: float
    engine: DatabaseEngine
    server_version: str | None = None
    error_code: str | None = None
    error_message: str | None = None


class SchemaInspectionResponse(BaseModel):
    """Response containing discovered schemas."""

    model_config = ConfigDict(frozen=True)

    workspace_id: uuid.UUID
    database: str
    schemas: list[str]


class TableInspectionResponse(BaseModel):
    """Response containing inspected tables and summary counts."""

    model_config = ConfigDict(frozen=True)

    workspace_id: uuid.UUID
    schema_name: str
    table_name: str
    object_type: str = "TABLE"
    column_count: int
    has_primary_key: bool
    foreign_key_count: int
    index_count: int
    comment: str | None = None


class CreateConnectionRequest(BaseModel):
    """Payload to configure a new database connection within a workspace."""

    name: str = Field(..., min_length=1, max_length=100, description="Display name for connection.")
    engine: DatabaseEngine
    database: str = Field(
        ..., min_length=1, description="Target database name or catalog identifier."
    )
    provider: DatabaseProvider = DatabaseProvider.GENERIC
    host: str | None = None
    port: int | None = None
    username: str | None = None
    password: str | None = None
    ssl_mode: str = "prefer"


class UpdateConnectionRequest(BaseModel):
    """Payload to update an existing database connection."""

    name: str | None = None
    database: str | None = None
    provider: DatabaseProvider | None = None
    host: str | None = None
    port: int | None = None
    username: str | None = None
    password: str | None = None
    ssl_mode: str | None = None


class ConnectionResponse(BaseModel):
    """Safe connection representation with redacted credentials."""

    model_config = ConfigDict(frozen=True)

    id: str
    workspace_id: str
    name: str
    engine: DatabaseEngine
    provider: DatabaseProvider
    database: str
    host: str | None = None
    port: int | None = None
    username: str | None = None
    has_password: bool = False
    ssl_mode: str = "prefer"
    status: str = "not_tested"
    last_tested_at: str | None = None
    last_inspected_at: str | None = None
    created_at: str
    updated_at: str | None = None
    error_message: str | None = None


class ConnectionListResponse(BaseModel):
    """List of connections authorized in a workspace."""

    model_config = ConfigDict(frozen=True)

    connections: list[ConnectionResponse]
    total_count: int
