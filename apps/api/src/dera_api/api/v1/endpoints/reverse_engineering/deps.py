"""DERA API — Phase 6.6 Reverse Engineering FastAPI Dependencies.

Provides dependency injection for reverse engineering services,
workspace header resolution, and tenant isolation validation.
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import Header, HTTPException, Query, Request, status

from dera_api.api.v1.endpoints.reverse_engineering.service import (
    ReverseEngineeringService,
    default_reverse_engineering_service,
)
from dera_api.auth.exceptions import (
    PermissionDeniedError,
    WorkspaceAccessDeniedError,
)
from dera_api.auth.policies import has_permission
from dera_api.auth.roles import Permission
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

    # Extract session token (Bearer header or cookie)
    from dera_api.auth.dependencies import extract_session_token
    from dera_api.auth.exceptions import (
        AccountDisabledError,
        AuthenticationRequiredError,
        SessionExpiredError,
        SessionRevokedError,
    )
    from dera_api.auth.tokens import hash_session_token
    from dera_api.repositories.sessions import SessionRepository
    from datetime import UTC, datetime

    token = extract_session_token(request)

    # Resolve database session factory
    session_factory = (
        getattr(request.app.state, "db_session_factory", None)
        if hasattr(request, "app") and hasattr(request.app, "state")
        else None
    )

    # Fail closed: In production / DB-backed configurations, authentication and DB verification are strictly mandatory
    if session_factory is None:
        # Check if running in a decoupled test environment without database
        # Even in detached environments, anonymous or untrusted access must fail closed if token is missing
        user_and_session = getattr(request.state, "user_and_session", None)
        if user_and_session is None and not token:
            raise AuthenticationRequiredError("Authentication required. Missing session token or credentials.")
        return str(ws_uuid)

    # Authoritative server-side verification with database
    if not token:
        # Check if request.state has user_and_session already injected
        user_and_session = getattr(request.state, "user_and_session", None)
        if not user_and_session:
            raise AuthenticationRequiredError("Authentication required. Missing session token.")
        current_user = user_and_session[0]
    else:
        async with session_factory() as db_session:
            token_hash = hash_session_token(token)
            session_repo = SessionRepository(db_session)
            user_session = await session_repo.get_by_token_hash(token_hash)
            if not user_session:
                raise AuthenticationRequiredError("Invalid or expired session token.")

            if user_session.revoked_at is not None:
                raise SessionRevokedError()

            now = datetime.now(UTC)
            expires_at = user_session.expires_at
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=UTC)
            if expires_at <= now:
                raise SessionExpiredError()

            current_user = user_session.user
            if current_user.status != "active":
                raise AccountDisabledError()

            # Cache authenticated user in request state
            request.state.user_and_session = (current_user, user_session)

    # Verify workspace existence, active status, and membership
    async with session_factory() as db_session:
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
