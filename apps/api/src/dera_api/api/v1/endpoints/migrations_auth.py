"""DERA API — Phase 9 Centralized Migration Authorization.

Provides typed authorization context and dependency injection for migration engineering
and governance operations. Enforces server-side authentication, active session verification,
workspace tenancy, active membership, and role-based permissions without client trust.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import Header, HTTPException, Query, Request, status

from dera_api.auth.dependencies import extract_session_token
from dera_api.auth.exceptions import (
    AccountDisabledError,
    AuthDomainException,
    AuthenticationRequiredError,
    PermissionDeniedError,
    SessionExpiredError,
    SessionRevokedError,
    WorkspaceAccessDeniedError,
)
from dera_api.auth.policies import ROLE_PERMISSIONS, has_permission
from dera_api.auth.roles import Permission, WorkspaceRole
from dera_api.auth.tokens import hash_session_token
from dera_api.repositories.memberships import MembershipRepository
from dera_api.repositories.sessions import SessionRepository
from dera_api.repositories.workspaces import WorkspaceRepository


@dataclass(frozen=True)
class MigrationAuthorizationContext:
    """Strongly-typed server-verified authorization context for migration operations."""

    user_id: uuid.UUID
    workspace_id: uuid.UUID
    membership_id: uuid.UUID
    role: str
    permissions: frozenset[str]
    current_user: Any
    workspace: Any
    membership: Any


def require_migration_auth(
    required_permission: Permission,
) -> Callable[..., Any]:
    """Dependency factory returning an async authorization validator for the specified permission."""

    async def _dependency(
        request: Request,
        x_workspace_id: Annotated[str | None, Header(alias="X-Workspace-Id")] = None,
        workspace_id_query: Annotated[str | None, Query(alias="workspace_id")] = None,
    ) -> MigrationAuthorizationContext:
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

        token = extract_session_token(request)

        # Resolve database session factory
        session_factory = (
            getattr(request.app.state, "db_session_factory", None)
            if hasattr(request, "app") and hasattr(request.app, "state")
            else None
        )

        user_and_session = getattr(request.state, "user_and_session", None)
        if user_and_session is None and not token:
            raise AuthenticationRequiredError("Authentication credentials are required.")

        if session_factory is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database service unavailable. Cannot verify authoritative migration authorization.",
            )

        try:
            async with session_factory() as db_session:
                if token:
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

                    request.state.user_and_session = (current_user, user_session)
                else:
                    current_user = user_and_session[0]
                    if current_user.status != "active":
                        raise AccountDisabledError()

                workspace_repo = WorkspaceRepository(db_session)
                workspace = await workspace_repo.get_by_id(ws_uuid)
                if not workspace or workspace.status != "active":
                    raise WorkspaceAccessDeniedError("Workspace does not exist or is inactive.")

                membership_repo = MembershipRepository(db_session)
                membership = await membership_repo.get_membership(workspace.id, current_user.id)
                if not membership or membership.status != "active":
                    raise WorkspaceAccessDeniedError(
                        "You are not an active member of this workspace."
                    )

                try:
                    ws_role = WorkspaceRole(membership.role.lower())
                    role_perms = frozenset(
                        p.value for p in ROLE_PERMISSIONS.get(ws_role, frozenset())
                    )
                except ValueError:
                    role_perms = frozenset()

                if not has_permission(membership.role, required_permission):
                    raise PermissionDeniedError(
                        f"Your role '{membership.role}' lacks the '{required_permission.value}' permission."
                    )

                auth_ctx = MigrationAuthorizationContext(
                    user_id=current_user.id,
                    workspace_id=workspace.id,
                    membership_id=membership.id,
                    role=membership.role,
                    permissions=role_perms,
                    current_user=current_user,
                    workspace=workspace,
                    membership=membership,
                )

                request.state.auth_context = auth_ctx
                request.state.workspace = workspace
                request.state.membership = membership
                request.state.user_role = membership.role

                return auth_ctx
        except (AuthDomainException, HTTPException):
            raise
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database authorization service failure. Request failed closed.",
            ) from exc

    return _dependency
