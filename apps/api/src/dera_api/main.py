"""DERA Application Backend Gateway.

FastAPI entrypoint providing health verification, version info,
and read-only database inspection endpoints.
"""

import dera
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from dera_api.core.config import get_settings
from dera_api.middleware.security import SecurityHeadersMiddleware

settings = get_settings()

app = FastAPI(
    title="DERA API",
    description="Deterministic Database Engineering & Reverse Analysis Platform API",
    version=dera.__version__,
)

# Attach security and CORS middleware
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check() -> dict[str, str]:
    """Returns the service health status."""
    return {"status": "healthy", "service": "dera-api", "version": dera.__version__}


@app.get("/info")
def platform_info() -> dict[str, str]:
    """Returns official platform identity and deterministic engineering principles."""
    return {
        "project": "DERA",
        "name": "Database Engineering & Reverse Analysis",
        "tagline": "Understand Every Schema. Engineer Every Change.",
        "maintainer": "Krishanth",
        "philosophy": "Deterministic, non-AI database reverse engineering",
        "version": dera.__version__,
    }


@app.get("/api/v1/meta")
def platform_meta() -> dict[str, object]:
    """Returns extended platform capabilities and deterministic constraints."""
    return {
        "name": settings.app_name,
        "version": settings.version,
        "environment": settings.environment,
        "zero_ai_policy": settings.zero_ai_policy_enforced,
        "read_only_enforced": settings.read_only_enforced,
        "supported_dialects": ["sqlite", "postgresql", "mysql", "mariadb"],
    }
