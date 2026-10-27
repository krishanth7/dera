"""DERA API — Version 1 System Endpoints.

Provides platform metadata, capability discovery, and ping probes under /api/v1.
"""

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends

from dera_api.core.config import ApiSettings
from dera_api.dependencies.common import get_app_settings
from dera_api.schemas.health import MetaResponse
from dera_api.schemas.system import SystemPingResponse

router = APIRouter(prefix="", tags=["System"])


@router.get(
    "/meta",
    response_model=MetaResponse,
    summary="Platform Capabilities & Architecture Metadata",
    description="Returns platform configuration, supported database dialects, and zero-AI policy status.",
)
def get_metadata(
    settings: Annotated[ApiSettings, Depends(get_app_settings)],
) -> MetaResponse:
    """Returns extended platform capabilities and deterministic constraints."""
    return MetaResponse(
        name=settings.app_name,
        version=settings.version,
        environment=settings.environment,
        zero_ai_policy=settings.zero_ai_policy_enforced,
        read_only_enforced=settings.read_only_enforced,
        supported_dialects=["sqlite", "postgresql", "mysql", "mariadb"],
    )


@router.get(
    "/ping",
    response_model=SystemPingResponse,
    summary="Low-Latency Heartbeat",
    description="Fast non-blocking ping verification endpoint.",
)
def ping() -> SystemPingResponse:
    """Returns low-latency heartbeat verification."""
    return SystemPingResponse(
        ping="pong",
        timestamp=datetime.now(UTC).isoformat(),
    )
