"""DERA Schemas — Authentication Contracts.

Defines Pydantic v2 request and response contracts for user registration,
login, session management, and current-user identity endpoints.
"""

import uuid
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

EmailAddress = Annotated[
    str,
    Field(
        min_length=5,
        max_length=254,
        pattern=r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$",
        description="User email address.",
        examples=["engineer@example.com"],
    ),
]


class RegisterRequest(BaseModel):
    """Payload for self-service user registration."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    email: EmailAddress
    password: str = Field(
        ...,
        min_length=12,
        max_length=128,
        description="NIST-compliant password (12-128 characters).",
        examples=["correct-horse-battery-staple-2026"],
    )


class LoginRequest(BaseModel):
    """Payload for user authentication."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    email: EmailAddress
    password: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description="User password.",
        examples=["correct-horse-battery-staple-2026"],
    )


class UserResponse(BaseModel):
    """Public representation of an authenticated user identity."""

    model_config = ConfigDict(from_attributes=True, frozen=True)

    id: uuid.UUID = Field(..., description="Unique user identifier.")
    email: str = Field(..., description="Normalized user email address.")
    status: str = Field(..., description="Account lifecycle status.")
    email_verified_at: datetime | None = Field(
        default=None,
        description="UTC timestamp of email verification.",
    )
    created_at: datetime = Field(..., description="UTC timestamp of account creation.")


class AuthResponse(BaseModel):
    """Authentication response payload containing user data and CSRF token."""

    model_config = ConfigDict(frozen=True)

    user: UserResponse = Field(..., description="Authenticated user account details.")
    session_id: uuid.UUID = Field(..., description="Unique session identifier.")
    csrf_token: str = Field(..., description="Anti-CSRF token for state-changing requests.")
    expires_at: datetime = Field(..., description="UTC timestamp when this session expires.")


class SessionResponse(BaseModel):
    """Public representation of an active user session."""

    model_config = ConfigDict(from_attributes=True, frozen=True)

    id: uuid.UUID = Field(..., description="Unique session record identifier.")
    ip_address: str | None = Field(default=None, description="Recorded client IP address.")
    user_agent: str | None = Field(default=None, description="Recorded client user agent.")
    created_at: datetime = Field(..., description="UTC timestamp when session was issued.")
    last_seen_at: datetime = Field(..., description="UTC timestamp of last session activity.")
    expires_at: datetime = Field(..., description="UTC timestamp when session expires.")
