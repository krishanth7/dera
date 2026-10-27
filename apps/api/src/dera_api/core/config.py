"""DERA API — Typed Application Configuration.

Defines typed configuration settings for the DERA API gateway using Pydantic v2
and pydantic-settings, supporting development, testing, and production profiles.
"""

from functools import lru_cache
from typing import Any

import dera
from pydantic import AliasChoices, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

VALID_ENVIRONMENTS = {"development", "testing", "production"}
VALID_LOG_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}


class ApiSettings(BaseSettings):
    """Typed application settings with strict validation for DERA API Gateway."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = Field(
        default="DERA API Gateway",
        validation_alias=AliasChoices("APP_NAME", "DERA_APP_NAME"),
        description="Public display name of the API gateway service.",
    )
    version: str = Field(
        default_factory=lambda: dera.__version__,
        validation_alias=AliasChoices("APP_VERSION", "DERA_VERSION"),
        description="Semantic version string of the platform.",
    )
    environment: str = Field(
        default="development",
        validation_alias=AliasChoices("APP_ENV", "DERA_ENV"),
        description="Deployment environment profile (development, testing, production).",
    )
    debug: bool = Field(
        default=False,
        validation_alias=AliasChoices("APP_DEBUG", "DERA_DEBUG"),
        description="Enable debug mode and verbose framework tracebacks.",
    )
    host: str = Field(
        default="127.0.0.1",
        validation_alias=AliasChoices("APP_HOST", "DERA_API_HOST"),
        description="Network interface for the ASGI server.",
    )
    port: int = Field(
        default=8000,
        validation_alias=AliasChoices("APP_PORT", "DERA_API_PORT"),
        description="Port for the HTTP listener (1-65535).",
    )
    log_level: str = Field(
        default="INFO",
        validation_alias=AliasChoices("APP_LOG_LEVEL", "DERA_LOG_LEVEL"),
        description="Standard logging verbosity level.",
    )
    api_prefix: str = Field(
        default="/api/v1",
        validation_alias=AliasChoices("APP_API_PREFIX", "DERA_API_PREFIX"),
        description="Root path prefix for versioned API endpoints.",
    )
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://127.0.0.1:3000"],
        validation_alias=AliasChoices("APP_CORS_ORIGINS", "DERA_CORS_ORIGINS"),
        description="Allowed CORS origins list.",
    )
    docs_enabled: bool | None = Field(
        default=None,
        validation_alias=AliasChoices("APP_DOCS_ENABLED", "DERA_DOCS_ENABLED"),
        description="Enable OpenAPI documentation endpoints (/docs, /redoc, /openapi.json).",
    )
    request_id_header: str = Field(
        default="X-Request-ID",
        validation_alias=AliasChoices("APP_REQUEST_ID_HEADER", "DERA_REQUEST_ID_HEADER"),
        description="Header name for HTTP request correlation tracking.",
    )
    read_only_enforced: bool = Field(
        default=True,
        validation_alias=AliasChoices("READ_ONLY_ENFORCED", "DERA_READ_ONLY_ENFORCED"),
        description="Enforces read-only inspection boundaries across database connectors.",
    )
    zero_ai_policy_enforced: bool = Field(
        default=True,
        validation_alias=AliasChoices("ZERO_AI_POLICY_ENFORCED", "DERA_ZERO_AI_POLICY_ENFORCED"),
        description="Deterministic zero-AI architectural constraint guarantee.",
    )

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        env = v.strip().lower()
        if env not in VALID_ENVIRONMENTS:
            raise ValueError(
                f"Invalid environment '{v}'. Allowed profiles: {sorted(VALID_ENVIRONMENTS)}"
            )
        return env

    @field_validator("port")
    @classmethod
    def validate_port(cls, v: int) -> int:
        if not (1 <= v <= 65535):
            raise ValueError(f"Port must be between 1 and 65535, got {v}")
        return v

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        lvl = v.strip().upper()
        if lvl not in VALID_LOG_LEVELS:
            raise ValueError(
                f"Invalid log level '{v}'. Allowed levels: {sorted(VALID_LOG_LEVELS)}"
            )
        return lvl

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            items = [item.strip() for item in v.split(",") if item.strip()]
            return items if items else ["http://localhost:3000"]
        if isinstance(v, list):
            return [str(item).strip() for item in v if str(item).strip()]
        return ["http://localhost:3000"]

    @model_validator(mode="after")
    def validate_production_restrictions(self) -> "ApiSettings":
        """Enforces defensive production security rules."""
        if self.environment == "production":
            if self.debug:
                raise ValueError("Debug mode is strictly prohibited in production environment")
            if any(origin == "*" for origin in self.cors_origins):
                raise ValueError(
                    "Wildcard CORS origins ('*') are strictly prohibited in production"
                )
            if self.docs_enabled is None:
                self.docs_enabled = False
        else:
            if self.docs_enabled is None:
                self.docs_enabled = True

        return self


@lru_cache(maxsize=1)
def get_settings() -> ApiSettings:
    """Return application settings singleton cached across invocations."""
    return ApiSettings()


def clear_settings_cache() -> None:
    """Clear cached settings singleton for testing and environment reloads."""
    get_settings.cache_clear()
