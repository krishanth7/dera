"""DERA API — Version 1 API Root Router.

Aggregates all modular sub-routers under the /api/v1 prefix and registers
standard RFC 9457 error response models in the OpenAPI specification.
"""

from fastapi import APIRouter

from dera_api.api.v1.endpoints.auth import router as auth_router
from dera_api.api.v1.endpoints.connections import router as connections_router
from dera_api.api.v1.endpoints.jobs import router as jobs_router
from dera_api.api.v1.endpoints.reverse_engineering import router as reverse_engineering_router
from dera_api.api.v1.endpoints.system import router as system_router
from dera_api.api.v1.endpoints.workspaces import router as workspaces_router
from dera_api.contracts.errors import ProblemDetail

api_v1_router = APIRouter(
    responses={
        400: {"model": ProblemDetail, "description": "Client Error / Bad Request"},
        401: {"model": ProblemDetail, "description": "Authentication Required or Invalid"},
        403: {"model": ProblemDetail, "description": "Forbidden / Access Denied"},
        404: {"model": ProblemDetail, "description": "Resource Not Found"},
        409: {"model": ProblemDetail, "description": "Resource Conflict"},
        422: {"model": ProblemDetail, "description": "Validation Failure (RFC 9457)"},
        429: {"model": ProblemDetail, "description": "Rate Limited"},
        500: {"model": ProblemDetail, "description": "Internal Server Error"},
    }
)
api_v1_router.include_router(system_router)
api_v1_router.include_router(auth_router)
api_v1_router.include_router(workspaces_router)
api_v1_router.include_router(jobs_router)
api_v1_router.include_router(reverse_engineering_router)
api_v1_router.include_router(connections_router)
