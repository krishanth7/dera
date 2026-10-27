"""DERA API — Application Exceptions and Safe Handlers.

Defines core exception types and centralized HTTP exception handlers
that prevent credential leaks, stack-trace exposure, and raw internal paths.
"""

from dera_api.core.logging import get_logger
from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = get_logger("dera_api.exceptions")


class DeraError(Exception):
    """Base exception for all DERA application errors."""

    def __init__(self, message: str, code: str = "DERA_ERROR", status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code


class DeraConfigurationError(DeraError):
    """Raised when application configuration is invalid or missing."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="CONFIG_ERROR", status_code=500)


class DeraReadinessError(DeraError):
    """Raised when application readiness checks fail."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="READINESS_FAILURE", status_code=503)


def get_request_id_from_request(request: Request) -> str | None:
    """Safely extracts correlation ID attached to request state."""
    return getattr(request.state, "request_id", None)


async def dera_exception_handler(request: Request, exc: DeraError) -> JSONResponse:
    """Handles domain DeraError exceptions returning structured JSON."""
    request_id = get_request_id_from_request(request)
    logger.warning(
        "Domain error [%s]: %s (request_id=%s)",
        exc.code,
        exc.message,
        request_id,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "request_id": request_id,
            }
        },
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handles request body/param validation errors safely."""
    request_id = get_request_id_from_request(request)
    logger.info("Request validation failed (request_id=%s): %s", request_id, exc.errors())
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request parameter or body validation failed.",
                "details": exc.errors(),
                "request_id": request_id,
            }
        },
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Handles standard HTTPExceptions cleanly."""
    request_id = get_request_id_from_request(request)
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": f"HTTP_{exc.status_code}",
                "message": exc.detail,
                "request_id": request_id,
            }
        },
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handles all unexpected errors without leaking stack traces or internal paths."""
    request_id = get_request_id_from_request(request)
    logger.error(
        "Unhandled server exception during request processing (request_id=%s): %s",
        request_id,
        exc,
        exc_info=True,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred while processing the request.",
                "request_id": request_id,
            }
        },
    )
