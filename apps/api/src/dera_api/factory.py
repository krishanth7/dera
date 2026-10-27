"""DERA API — Authoritative Application Factory.

Builds and configures deterministic FastAPI application instances with typed settings,
modern lifespan lifecycle, defensive middlewares, and structured exception handlers.
"""

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from dera_api.api.v1.router import api_v1_router
from dera_api.core.config import ApiSettings, get_settings
from dera_api.core.exceptions import (
    DeraError,
    dera_exception_handler,
    http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from dera_api.core.lifespan import get_application_readiness, lifespan
from dera_api.core.logging import configure_logging
from dera_api.middleware.request_id import RequestIDMiddleware
from dera_api.middleware.security import SecurityHeadersMiddleware
from dera_api.schemas.health import (
    HealthResponse,
    LivenessResponse,
    ReadinessResponse,
    ReadinessSubsystems,
)
from dera_api.schemas.system import PlatformInfoResponse


def create_app(settings: ApiSettings | None = None) -> FastAPI:
    """Creates a deterministic, production-ready FastAPI application instance.

    Args:
        settings: Optional typed application configuration settings.
                  Defaults to the singleton provided by get_settings().

    Returns:
        Configured FastAPI application instance.
    """
    app_settings = settings or get_settings()

    # Configure root logger with application level
    configure_logging(app_settings.log_level)

    # Determine OpenAPI documentation URLs based on configuration
    docs_url = "/docs" if app_settings.docs_enabled else None
    redoc_url = "/redoc" if app_settings.docs_enabled else None
    openapi_url = "/openapi.json" if app_settings.docs_enabled else None

    app = FastAPI(
        title=app_settings.app_name,
        description="Deterministic Database Engineering & Reverse Analysis Platform API",
        version=app_settings.version,
        lifespan=lifespan,
        docs_url=docs_url,
        redoc_url=redoc_url,
        openapi_url=openapi_url,
        contact={
            "name": "DERA Maintainers",
            "url": "https://github.com/krishanth7/dera",
        },
        license_info={
            "name": "MIT",
            "url": "https://opensource.org/licenses/MIT",
        },
    )

    # Attach settings to application state
    app.state.settings = app_settings

    # 1. Attach Middlewares (Order of execution: SecurityHeaders -> RequestID -> CORS)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestIDMiddleware, header_name=app_settings.request_id_header)

    has_wildcard_cors = any(origin == "*" for origin in app_settings.cors_origins)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=app_settings.cors_origins,
        allow_credentials=not has_wildcard_cors,
        allow_methods=["GET", "POST", "OPTIONS", "HEAD"],
        allow_headers=["*"],
        expose_headers=[app_settings.request_id_header],
    )

    # 2. Register Global Exception Handlers
    app.add_exception_handler(DeraError, dera_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)

    # 3. Register Root Health & Identity Endpoints
    @app.get(
        "/health/live",
        response_model=LivenessResponse,
        tags=["Health"],
        summary="Service Process Liveness",
        description="Verifies that the API service process is active and executing.",
    )
    def liveness_check() -> LivenessResponse:
        return LivenessResponse(
            status="ok",
            service="dera-api",
            version=app_settings.version,
        )

    @app.get(
        "/health/ready",
        response_model=ReadinessResponse,
        tags=["Health"],
        summary="Service Operational Readiness",
        description="Verifies that the API is fully prepared to serve requests without claiming uninitialized dependencies.",
    )
    def readiness_check(request: Request) -> JSONResponse | ReadinessResponse:
        readiness_data = get_application_readiness(request.app)
        is_ready = readiness_data["ready"]

        response_body = ReadinessResponse(
            status="ok" if is_ready else "not_ready",
            service="dera-api",
            version=app_settings.version,
            ready=is_ready,
            subsystems=ReadinessSubsystems(
                application_state=readiness_data["subsystems"]["application_state"],
                database_connectors=readiness_data["subsystems"]["database_connectors"],
                background_workers=readiness_data["subsystems"]["background_workers"],
            ),
        )

        status_code = status.HTTP_200_OK if is_ready else status.HTTP_503_SERVICE_UNAVAILABLE
        return JSONResponse(status_code=status_code, content=response_body.model_dump())

    @app.get(
        "/health",
        response_model=HealthResponse,
        tags=["Health"],
        summary="Legacy Health Check",
        description="Backward-compatible liveness probe for existing infrastructure.",
    )
    def legacy_health_check() -> HealthResponse:
        return HealthResponse(
            status="healthy",
            service="dera-api",
            version=app_settings.version,
        )

    @app.get(
        "/info",
        response_model=PlatformInfoResponse,
        tags=["System"],
        summary="Platform Identity & Principles",
        description="Returns official platform identity, maintainer details, and non-AI philosophy.",
    )
    def platform_info() -> PlatformInfoResponse:
        return PlatformInfoResponse(
            project="DERA",
            name="Database Engineering & Reverse Analysis",
            tagline="Understand Every Schema. Engineer Every Change.",
            maintainer="Krishanth",
            philosophy="Deterministic, non-AI database reverse engineering",
            version=app_settings.version,
        )

    # 4. Mount Versioned API Routes (/api/v1)
    app.include_router(api_v1_router, prefix=app_settings.api_prefix)

    return app
