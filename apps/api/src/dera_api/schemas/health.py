"""DERA API — Health and Metadata Response Models.

Pydantic v2 schemas for liveness, readiness, and platform capability endpoints.
"""

from pydantic import BaseModel, ConfigDict, Field


class LivenessResponse(BaseModel):
    """Schema for process liveness probe (/health/live)."""

    model_config = ConfigDict(frozen=True)

    status: str = Field(default="ok", description="Service process status.")
    service: str = Field(default="dera-api", description="Service identifier.")
    version: str = Field(..., description="Canonical platform version.")


class ReadinessSubsystems(BaseModel):
    """Subsystem status reported truthfully during readiness checks."""

    model_config = ConfigDict(frozen=True)

    application_state: str = Field(description="Internal lifecycle state.")
    database_connectors: str = Field(description="Database connector readiness.")
    background_workers: str = Field(description="Background task queue readiness.")
    platform_database: str = Field(
        default="not_configured",
        description="Internal platform database readiness status.",
    )


class ReadinessResponse(BaseModel):
    """Schema for application readiness probe (/health/ready)."""

    model_config = ConfigDict(frozen=True)

    status: str = Field(default="ok", description="Overall readiness status.")
    service: str = Field(default="dera-api", description="Service identifier.")
    version: str = Field(..., description="Canonical platform version.")
    ready: bool = Field(..., description="Readiness boolean flag.")
    subsystems: ReadinessSubsystems = Field(..., description="Detailed subsystem states.")


class HealthResponse(BaseModel):
    """Schema for legacy backward-compatible health check (/health)."""

    model_config = ConfigDict(frozen=True)

    status: str = Field(default="healthy", description="Service health state.")
    service: str = Field(default="dera-api", description="Service identifier.")
    version: str = Field(..., description="Canonical platform version.")


class MetaResponse(BaseModel):
    """Schema for platform metadata and capabilities (/api/v1/meta)."""

    model_config = ConfigDict(frozen=True)

    name: str = Field(..., description="Service application name.")
    version: str = Field(..., description="Application version.")
    environment: str = Field(..., description="Active environment profile.")
    zero_ai_policy: bool = Field(..., description="Enforcement of deterministic zero-AI policy.")
    read_only_enforced: bool = Field(..., description="Enforcement of read-only DB inspection.")
    supported_dialects: list[str] = Field(..., description="List of supported database dialects.")
