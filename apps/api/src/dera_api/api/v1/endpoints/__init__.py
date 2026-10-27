"""DERA API — V1 Endpoints."""

from dera_api.api.v1.endpoints.auth import router as auth_router
from dera_api.api.v1.endpoints.jobs import router as jobs_router
from dera_api.api.v1.endpoints.system import router as system_router
from dera_api.api.v1.endpoints.workspaces import router as workspaces_router

__all__ = ["auth_router", "jobs_router", "system_router", "workspaces_router"]
