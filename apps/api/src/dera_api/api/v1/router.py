"""DERA API — Version 1 API Root Router.

Aggregates all modular sub-routers under the /api/v1 prefix and registers
standard RFC 9457 error response models in the OpenAPI specification.
"""

from fastapi import APIRouter

from dera_api.api.v1.endpoints.system import router as system_router
from dera_api.contracts.errors import ProblemDetail

api_v1_router = APIRouter(
    responses={
        400: {"model": ProblemDetail, "description": "Client Error / Bad Request"},
        404: {"model": ProblemDetail, "description": "Resource Not Found"},
        422: {"model": ProblemDetail, "description": "Validation Failure (RFC 9457)"},
        500: {"model": ProblemDetail, "description": "Internal Server Error"},
    }
)
api_v1_router.include_router(system_router)
