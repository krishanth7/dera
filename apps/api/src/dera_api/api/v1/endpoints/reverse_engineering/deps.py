"""DERA API — Phase 6.6 Reverse Engineering FastAPI Dependencies.

Provides dependency injection for reverse engineering services,
workspace header resolution, and tenant isolation validation.
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import Depends, Header, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from dera_api.api.v1.endpoints.reverse_engineering.service import (
    ReverseEngineeringService,
    default_reverse_engineering_service,
)
from dera_api.auth.dependencies import get_current_user
from dera_api.auth.exceptions import (
    PermissionDeniedError,
    WorkspaceAccessDeniedError,
)
from dera_api.auth.policies import has_permission
from dera_api.auth.roles import Permission
from dera_api.db.dependencies import get_db_session
from dera_api.db.models.identity import User
from dera_api.repositories.memberships import MembershipRepository
from dera_api.repositories.workspaces import WorkspaceRepository


def get_re_service(request: Request) -> ReverseEngineeringService:
    """Retrieve reverse engineering application service singleton from application state."""
    if hasattr(request, "app") and hasattr(request.app, "state"):
        if hasattr(request.app.state, "reverse_engineering_service"):
            return request.app.state.reverse_engineering_service
    return default_reverse_engineering_service


async def resolve_authorized_workspace_id(
    request: Request,
    x_workspace_id: Annotated[str | None, Header(alias="X-Workspace-Id")] = None,
    workspace_id_query: Annotated[str | None, Query(alias="workspace_id")] = None,
    current_user: Annotated[User | None, Depends(get_current_user)] = None,
    db_session: Annotated[AsyncSession | None, Depends(get_db_session)] = None,
) -> str:
    """Resolve and authorize workspace ID from header or query parameter.

    Enforces:
    1. Presence of workspace context.
    2. Valid UUID formatting.
    3. Active workspace status in DB (if DB available).
    4. Active membership of authenticated user (if DB available).
    5. Schema read permission.
    """
    raw_ws_id = x_workspace_id or workspace_id_query
    if not raw_ws_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing required 'X-Workspace-Id' header or 'workspace_id' query parameter.",
        )

    try:
        ws_uuid = uuid.UUID(raw_ws_id.strip())
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid workspace ID format: '{raw_ws_id}'. Must be a valid UUID.",
        ) from None

    # If full DB and auth context is provided, enforce workspace and membership checks
    if db_session is not None and current_user is not None:
        workspace_repo = WorkspaceRepository(db_session)
        workspace = await workspace_repo.get_by_id(ws_uuid)
        if not workspace or workspace.status != "active":
            raise WorkspaceAccessDeniedError("Workspace does not exist or is inactive.")

        membership_repo = MembershipRepository(db_session)
        membership = await membership_repo.get_membership(workspace.id, current_user.id)
        if not membership or membership.status != "active":
            raise WorkspaceAccessDeniedError("You are not an active member of this workspace.")

        if not has_permission(membership.role, Permission.SCHEMA_READ):
            raise PermissionDeniedError(
                f"Your role '{membership.role}' lacks the '{Permission.SCHEMA_READ}' permission."
            )

    return str(ws_uuid)
