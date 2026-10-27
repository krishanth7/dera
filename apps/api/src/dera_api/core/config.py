"""DERA API — Typed Application Configuration.

Defines typed configuration settings for the DERA API gateway using Pydantic v2
and pydantic-settings, supporting development, testing, and production profiles.
"""

import re
from functools import lru_cache
from typing import Any
from urllib.parse import urlsplit, urlunsplit

import dera
from pydantic import AliasChoices, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

VALID_ENVIRONMENTS = {"development", "testing", "production"}
VALID_LOG_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
VALID_SSL_MODES = {"disable", "allow", "prefer", "require", "verify-ca", "verify-full"}


class ApiSettings(BaseSettings):
    """Typed application settings with strict validation for DERA API Gateway."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        populate_by_name=True,
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

    # ------------------------------------------------------------------
    # Phase 4.3: Internal Platform PostgreSQL Database Settings
    # ------------------------------------------------------------------
    database_url: str | None = Field(
        default=None,
        validation_alias=AliasChoices("DERA_PLATFORM_DATABASE_URL", "DATABASE_URL"),
        description="Async connection URL for the internal DERA platform PostgreSQL database.",
    )
    db_pool_size: int = Field(
        default=10,
        ge=1,
        le=100,
        validation_alias=AliasChoices("DERA_DB_POOL_SIZE", "DB_POOL_SIZE"),
        description="Base connection pool size for application database operations.",
    )
    db_max_overflow: int = Field(
        default=5,
        ge=0,
        le=50,
        validation_alias=AliasChoices("DERA_DB_MAX_OVERFLOW", "DB_MAX_OVERFLOW"),
        description="Maximum transient overflow connections beyond base pool.",
    )
    db_pool_timeout: float = Field(
        default=30.0,
        ge=1.0,
        le=300.0,
        validation_alias=AliasChoices("DERA_DB_POOL_TIMEOUT", "DB_POOL_TIMEOUT"),
        description="Timeout in seconds to wait when acquiring a connection from the pool.",
    )
    db_pool_recycle: int = Field(
        default=1800,
        ge=60,
        le=86400,
        validation_alias=AliasChoices("DERA_DB_POOL_RECYCLE", "DB_POOL_RECYCLE"),
        description="Recycle connections after this duration in seconds (default 30 minutes).",
    )
    db_connect_timeout: float = Field(
        default=10.0,
        ge=1.0,
        le=60.0,
        validation_alias=AliasChoices("DERA_DB_CONNECT_TIMEOUT", "DB_CONNECT_TIMEOUT"),
        description="Connection acquisition timeout in seconds for new network sockets.",
    )
    db_statement_timeout_ms: int = Field(
        default=30000,
        ge=100,
        le=3600000,
        validation_alias=AliasChoices("DERA_DB_STATEMENT_TIMEOUT_MS", "DB_STATEMENT_TIMEOUT_MS"),
        description="Server-side PostgreSQL statement timeout in milliseconds.",
    )
    db_ssl_mode: str = Field(
        default="prefer",
        validation_alias=AliasChoices("DERA_DB_SSL_MODE", "DB_SSL_MODE"),
        description="SSL transport security mode for PostgreSQL connections.",
    )
    db_echo: bool = Field(
        default=False,
        validation_alias=AliasChoices("DERA_DB_ECHO", "DB_ECHO"),
        description="Enable SQLAlchemy SQL query echo logging (strictly non-production).",
    )

    @property
    def has_database_configured(self) -> bool:
        """Returns True if a platform database URL has been explicitly specified."""
        return bool(self.database_url and self.database_url.strip())

    @property
    def sanitized_database_url(self) -> str:
        """Returns the database URL with authentication credentials securely masked."""
        if not self.database_url:
            return "not-configured"
        try:
            parts = urlsplit(self.database_url)
            if parts.password:
                netloc = parts.netloc.replace(f":{parts.password}@", ":***@")
                return urlunsplit((parts.scheme, netloc, parts.path, parts.query, parts.fragment))
            return self.database_url
        except Exception:
            return re.sub(r"://([^:]+):([^@]+)@", r"://\1:***@", self.database_url)

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
            raise ValueError(f"Invalid log level '{v}'. Allowed levels: {sorted(VALID_LOG_LEVELS)}")
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

    @field_validator("db_ssl_mode")
    @classmethod
    def validate_db_ssl_mode(cls, v: str) -> str:
        mode = v.strip().lower()
        if mode not in VALID_SSL_MODES:
            raise ValueError(f"Invalid db_ssl_mode '{v}'. Allowed modes: {sorted(VALID_SSL_MODES)}")
        return mode

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
            if self.db_echo:
                raise ValueError(
                    "Database SQL query echo (db_echo) is strictly prohibited in production"
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
