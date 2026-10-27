"""DERA API — Health & Metadata Response Schemas."""

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """System health check response model."""

    status: str = Field(default="healthy", description="System operational status")
    service: str = Field(default="dera-api", description="Service identifier")
    version: str = Field(default="0.1.0-dev", description="Service release version")
    deterministic_engine: bool = Field(
        default=True, description="Strict non-AI deterministic execution active"
    )


class MetaResponse(BaseModel):
    """Platform metadata response model."""

    name: str = Field(default="DERA — Database Engineering & Reverse Analysis")
    version: str = Field(default="0.1.0-dev")
    architecture: str = Field(default="modular-monolith")
    zero_ai_policy: bool = Field(default=True)
    supported_dialects: list[str] = Field(
        default_factory=lambda: ["sqlite", "postgresql", "mysql", "mariadb"]
    )
