"""DERA API — Phase 6.6 Reverse Engineering Endpoints Aggregator.

Aggregates all reverse engineering route modules into a unified router
under the `/reverse-engineering` prefix.
"""

from fastapi import APIRouter

from dera_api.api.v1.endpoints.reverse_engineering.columns import router as columns_router
from dera_api.api.v1.endpoints.reverse_engineering.constraints import router as constraints_router
from dera_api.api.v1.endpoints.reverse_engineering.cycles import router as cycles_router
from dera_api.api.v1.endpoints.reverse_engineering.dependencies import router as dependencies_router
from dera_api.api.v1.endpoints.reverse_engineering.diagnostics import router as diagnostics_router
from dera_api.api.v1.endpoints.reverse_engineering.exports import router as exports_router
from dera_api.api.v1.endpoints.reverse_engineering.namespaces import router as namespaces_router
from dera_api.api.v1.endpoints.reverse_engineering.relationships import (
    router as relationships_router,
)
from dera_api.api.v1.endpoints.reverse_engineering.schemas import router as schemas_router
from dera_api.api.v1.endpoints.reverse_engineering.snapshots import router as snapshots_router
from dera_api.api.v1.endpoints.reverse_engineering.tables import router as tables_router

router = APIRouter(prefix="/reverse-engineering", tags=["Reverse Engineering"])

router.include_router(schemas_router)
router.include_router(namespaces_router)
router.include_router(tables_router)
router.include_router(columns_router)
router.include_router(constraints_router)
router.include_router(relationships_router)
router.include_router(dependencies_router)
router.include_router(cycles_router)
router.include_router(snapshots_router)
router.include_router(exports_router)
router.include_router(diagnostics_router)

__all__ = ["router"]
