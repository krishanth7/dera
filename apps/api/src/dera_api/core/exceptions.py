"""DERA API — Application Exceptions and RFC 9457 Problem Handlers.

Defines the core domain exception hierarchy and centralized HTTP exception handlers
emitting RFC 9457 Problem Details (application/problem+json) while preventing
credential leaks, stack-trace exposure, and internal path disclosures.
"""

from typing import Any

from dera_api.contracts.errors import (
    PROBLEM_JSON_MEDIA_TYPE,
    ErrorCode,
    FieldErrorDetail,
)
from dera_api.core.logging import get_logger
from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = get_logger("dera_api.exceptions")


class DeraError(Exception):
    """Base exception for all DERA domain errors."""

    def __init__(
        self,
        message: str,
        code: str | ErrorCode = ErrorCode.INTERNAL_ERROR,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        detail: str | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = str(code)
        self.status_code = status_code
        self.detail = detail or message


class ValidationDomainError(DeraError):
    """Raised when domain validation rules are violated."""

    def __init__(self, message: str, detail: str | None = None) -> None:
        super().__init__(
            message=message,
            code=ErrorCode.VALIDATION_ERROR,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
        )


class ResourceNotFoundError(DeraError):
    """Raised when a requested resource does not exist."""

    def __init__(
        self,
        message: str = "Requested resource not found",
        resource_type: str | None = None,
        resource_id: str | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code=ErrorCode.RESOURCE_NOT_FOUND,
            status_code=status.HTTP_404_NOT_FOUND,
        )
        self.resource_type = resource_type
        self.resource_id = resource_id
        self.details = {
            "resource_type": resource_type,
            "resource_id": resource_id,
        }


class ConflictError(DeraError):
    """Raised when an operation conflicts with current resource state."""

    def __init__(self, message: str) -> None:
        super().__init__(
            message=message,
            code=ErrorCode.CONFLICT,
            status_code=status.HTTP_409_CONFLICT,
        )


class DependencyUnavailableError(DeraError):
    """Raised when a required external system or database is unavailable."""

    def __init__(self, message: str) -> None:
        super().__init__(
            message=message,
            code=ErrorCode.DEPENDENCY_UNAVAILABLE,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )


class DeraConfigurationError(DeraError):
    """Raised when application configuration is invalid or missing."""

    def __init__(self, message: str) -> None:
        super().__init__(
            message=message,
            code="CONFIG_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


class DeraReadinessError(DeraError):
    """Raised when application readiness checks fail."""

    def __init__(self, message: str) -> None:
        super().__init__(
            message=message,
            code=ErrorCode.SERVICE_UNAVAILABLE,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )


def get_request_id_from_request(request: Request) -> str | None:
    """Safely extracts correlation ID attached to request state."""
    return getattr(request.state, "request_id", None)


def normalize_validation_errors(errors: list[dict[str, Any]]) -> list[FieldErrorDetail]:
    """Normalizes raw Pydantic validation errors into standard FieldErrorDetail contracts."""
    normalized: list[FieldErrorDetail] = []
    for err in errors:
        loc = err.get("loc", ())
        field_path = ".".join(str(p) for p in loc) if loc else "request"

        err_type = str(err.get("type", "invalid"))
        code = err_type.upper().replace(".", "_").replace(" ", "_")
        message = err.get("msg", "Validation error occurred.")

        # Extract safe constraint without leaking raw input values
        ctx = err.get("ctx", {})
        constraint = None
        if ctx:
            for k in ("le", "ge", "lt", "gt", "min_length", "max_length", "expected"):
                if k in ctx:
                    constraint = f"{k}={ctx[k]}"
                    break

        normalized.append(
            FieldErrorDetail(
                field=field_path,
                code=code,
                message=message,
                constraint=constraint,
            )
        )
    return normalized


def build_problem_response(
    status_code: int,
    title: str,
    detail: str,
    code: str,
    request: Request,
    errors: list[FieldErrorDetail] | None = None,
) -> JSONResponse:
    """Constructs RFC 9457 compliant JSONResponse with backward compatibility envelope."""
    request_id = get_request_id_from_request(request)
    instance = str(request.url.path) if hasattr(request, "url") else None

    payload: dict[str, Any] = {
        "type": "about:blank",
        "title": title,
        "status": status_code,
        "detail": detail,
        "instance": instance,
        "code": code,
        "request_id": request_id,
        # Backward compatibility envelope for Phase 4.1 clients
        "error": {
            "code": code,
            "message": detail,
            "request_id": request_id,
        },
    }

    if errors:
        payload["errors"] = [e.model_dump(exclude_none=True) for e in errors]
        payload["error"]["details"] = payload["errors"]

    return JSONResponse(
        status_code=status_code,
        content=payload,
        media_type=PROBLEM_JSON_MEDIA_TYPE,
    )


async def dera_exception_handler(request: Request, exc: DeraError) -> JSONResponse:
    """Handles domain DeraError exceptions returning RFC 9457 Problem Details."""
    request_id = get_request_id_from_request(request)
    logger.warning(
        "Domain error [%s]: %s (request_id=%s)",
        exc.code,
        exc.message,
        request_id,
    )
    title_map = {
        400: "Bad Request",
        404: "Resource Not Found",
        405: "Method Not Allowed",
        409: "Conflict",
        415: "Unsupported Media Type",
        422: "Validation Failed",
        429: "Too Many Requests",
        500: "Internal Server Error",
        503: "Service Unavailable",
    }
    title = title_map.get(exc.status_code, "Application Error")
    return build_problem_response(
        status_code=exc.status_code,
        title=title,
        detail=exc.message,
        code=exc.code,
        request=request,
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handles request validation failures returning RFC 9457 Problem Details."""
    request_id = get_request_id_from_request(request)
    normalized = normalize_validation_errors(exc.errors())
    logger.info("Request validation failed (request_id=%s): %d errors", request_id, len(normalized))

    return build_problem_response(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        title="Validation Failed",
        detail="The request contains invalid or unprocessable parameters.",
        code=ErrorCode.VALIDATION_ERROR,
        request=request,
        errors=normalized,
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Handles standard Starlette/FastAPI HTTPExceptions cleanly."""
    get_request_id_from_request(request)
    code_map = {
        400: ErrorCode.MALFORMED_REQUEST,
        404: ErrorCode.RESOURCE_NOT_FOUND,
        405: ErrorCode.METHOD_NOT_ALLOWED,
        409: ErrorCode.CONFLICT,
        415: ErrorCode.UNSUPPORTED_MEDIA_TYPE,
        429: ErrorCode.RATE_LIMITED,
        503: ErrorCode.SERVICE_UNAVAILABLE,
    }
    code = code_map.get(exc.status_code, f"HTTP_{exc.status_code}")

    title_map = {
        400: "Bad Request",
        404: "Resource Not Found",
        405: "Method Not Allowed",
        409: "Conflict",
        415: "Unsupported Media Type",
        429: "Too Many Requests",
        503: "Service Unavailable",
    }
    title = title_map.get(exc.status_code, "HTTP Error")

    return build_problem_response(
        status_code=exc.status_code,
        title=title,
        detail=str(exc.detail),
        code=code,
        request=request,
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handles unexpected server errors without leaking stack traces or internal paths."""
    request_id = get_request_id_from_request(request)
    logger.error(
        "Unhandled server exception during request processing (request_id=%s): %s",
        request_id,
        exc,
        exc_info=True,
    )
    return build_problem_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        title="Internal Server Error",
        detail="An unexpected error occurred while processing the request.",
        code=ErrorCode.INTERNAL_ERROR,
        request=request,
    )


def register_exception_handlers(app: Any) -> None:
    """Registers standard DERA exception handlers on the FastAPI app instance."""
    app.add_exception_handler(DeraError, dera_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
