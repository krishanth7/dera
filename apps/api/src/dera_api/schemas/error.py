"""DERA API — Standardized Error Response Schemas.

Pydantic v2 schemas for client-facing error payloads.
"""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ErrorDetail(BaseModel):
    """Detailed error object containing code, message, and optional request ID."""

    model_config = ConfigDict(frozen=True)

    code: str = Field(..., description="Machine-readable error classification code.")
    message: str = Field(..., description="Human-readable safe explanation of the error.")
    request_id: str | None = Field(default=None, description="Request correlation identifier.")
    details: Any = Field(default=None, description="Optional structured validation details.")


class ErrorResponse(BaseModel):
    """Top-level error payload wrapper."""

    model_config = ConfigDict(frozen=True)

    error: ErrorDetail = Field(..., description="Error detail object.")
