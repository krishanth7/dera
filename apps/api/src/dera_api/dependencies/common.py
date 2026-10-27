"""DERA API — Reusable Dependency Injection Providers.

Provides typed FastAPI dependencies for configuration, request context,
and future services without global state or circular imports.
"""

from fastapi import Request

from dera_api.core.config import ApiSettings, get_settings


def get_app_settings(request: Request) -> ApiSettings:
    """Provides application configuration from request app state or cached singleton."""
    return getattr(request.app.state, "settings", None) or get_settings()


def get_current_request_id(request: Request) -> str | None:
    """Provides the active correlation ID attached to request state."""
    return getattr(request.state, "request_id", None)
