"""DERA API — Application Configuration.

Defines typed configuration settings for the DERA API gateway.
"""

from dataclasses import dataclass, field
import os
from typing import List


@dataclass(frozen=True)
class ApiSettings:
    """Immutable API configuration settings."""

    app_name: str = "DERA API Gateway"
    version: str = "0.1.0-dev"
    environment: str = os.getenv("DERA_ENV", "development")
    api_prefix: str = "/api/v1"
    host: str = os.getenv("DERA_API_HOST", "127.0.0.1")
    port: int = int(os.getenv("DERA_API_PORT", "8000"))
    cors_origins: List[str] = field(
        default_factory=lambda: [
            origin.strip()
            for origin in os.getenv("DERA_CORS_ORIGINS", "http://localhost:3000").split(",")
        ]
    )
    read_only_enforced: bool = True
    zero_ai_policy_enforced: bool = True


def get_settings() -> ApiSettings:
    """Return application settings singleton."""
    return ApiSettings()
