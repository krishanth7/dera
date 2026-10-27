"""DERA API — Response Metadata Contracts.

Defines canonical metadata accompanying all enveloped responses and error payloads.
"""

from datetime import UTC, datetime

import dera
from pydantic import BaseModel, ConfigDict, Field


class ResponseMetadata(BaseModel):
    """Canonical metadata included on enveloped responses."""

    model_config = ConfigDict(frozen=True)

    request_id: str | None = Field(
        default=None,
        description="Unique correlation identifier for the request.",
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="ISO 8601 UTC timestamp of response generation.",
    )
    version: str = Field(
        default_factory=lambda: dera.__version__,
        description="Canonical semantic version string of the platform.",
    )
