"""DERA API — System and Ping Response Models.

Pydantic v2 schemas for system identity and heartbeat endpoints.
"""

from pydantic import BaseModel, ConfigDict, Field


class PlatformInfoResponse(BaseModel):
    """Schema for platform identity information (/info)."""

    model_config = ConfigDict(frozen=True)

    project: str = Field(default="DERA")
    name: str = Field(default="Database Engineering & Reverse Analysis")
    tagline: str = Field(default="Understand Every Schema. Engineer Every Change.")
    maintainer: str = Field(default="Krishanth")
    philosophy: str = Field(default="Deterministic, non-AI database reverse engineering")
    version: str = Field(..., description="Canonical platform version.")


class SystemPingResponse(BaseModel):
    """Schema for low-latency ping probe (/api/v1/ping)."""

    model_config = ConfigDict(frozen=True)

    ping: str = Field(default="pong", description="Heartbeat response token.")
    timestamp: str = Field(..., description="ISO 8601 UTC timestamp of the probe response.")
