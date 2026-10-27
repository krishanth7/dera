"""DERA API — Version 1 API Root Router.

Aggregates all modular sub-routers under the /api/v1 prefix.
"""

from fastapi import APIRouter

from dera_api.api.v1.endpoints.system import router as system_router

api_v1_router = APIRouter()
api_v1_router.include_router(system_router)
