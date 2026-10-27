"""DERA Schemas — Workspace and Membership Contracts.

Defines Pydantic v2 request and response contracts for multi-tenant workspace
creation, retrieval, and membership management.
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
        examples=["colleague@example.com"],
    ),
]


class CreateWorkspaceRequest(BaseModel):
    """Payload for creating a new multi-tenant workspace."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Human-readable workspace display name.",
        examples=["Engineering Core"],
    )
    slug: str = Field(
        ...,
        min_length=2,
        max_length=64,
        pattern=r"^[a-z0-9][a-z0-9-_]*[a-z0-9]$",
        description="URL-safe unique workspace identifier slug.",
        examples=["engineering-core"],
    )


class WorkspaceResponse(BaseModel):
    """Public representation of a workspace entity."""

    model_config = ConfigDict(from_attributes=True, frozen=True)

    id: uuid.UUID = Field(..., description="Unique workspace identifier.")
    name: str = Field(..., description="Workspace display name.")
    slug: str = Field(..., description="Workspace URL slug.")
    status: str = Field(..., description="Workspace status.")
    created_at: datetime = Field(..., description="UTC creation timestamp.")
    updated_at: datetime = Field(..., description="UTC modification timestamp.")
    current_user_role: str | None = Field(
        default=None,
        description="The authenticated user's role in this workspace.",
    )


class MembershipResponse(BaseModel):
    """Public representation of a user's membership within a workspace."""

    model_config = ConfigDict(from_attributes=True, frozen=True)

    id: uuid.UUID = Field(..., description="Unique membership identifier.")
    workspace_id: uuid.UUID = Field(..., description="Workspace identifier.")
    user_id: uuid.UUID = Field(..., description="Member user identifier.")
    user_email: str | None = Field(default=None, description="Member user email address.")
    role: str = Field(..., description="Assigned role: owner, admin, editor, viewer.")
    status: str = Field(..., description="Membership status: active, invited, suspended.")
    created_at: datetime = Field(..., description="UTC creation timestamp.")
    updated_at: datetime = Field(..., description="UTC modification timestamp.")


class AddMemberRequest(BaseModel):
    """Payload for adding or inviting a user to a workspace."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    email: EmailAddress
    role: str = Field(
        default="viewer",
        pattern=r"^(owner|admin|editor|viewer)$",
        description="Assigned role for the new member.",
        examples=["editor"],
    )


class UpdateMemberRoleRequest(BaseModel):
    """Payload for modifying an existing member's workspace role."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    role: str = Field(
        ...,
        pattern=r"^(owner|admin|editor|viewer)$",
        description="New role to assign: owner, admin, editor, viewer.",
        examples=["admin"],
    )
