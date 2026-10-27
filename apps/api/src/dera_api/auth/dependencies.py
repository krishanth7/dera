"""DERA Auth — FastAPI Authentication & Authorization Dependencies.

Provides dependency injection for resolving the current authenticated user,
enforcing active session status, verifying CSRF tokens on state-changing cookie requests,
and validating workspace-scoped permissions.
"""

import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from dera_api.auth.exceptions import (
    AccountDisabledError,
    AuthenticationRequiredError,
    CsrfValidationError,
    PermissionDeniedError,
    SessionExpiredError,
    SessionRevokedError,
    WorkspaceAccessDeniedError,
)
from dera_api.auth.policies import has_permission
from dera_api.auth.roles import Permission
from dera_api.auth.tokens import constant_time_compare, hash_session_token
from dera_api.core.config import get_settings
from dera_api.db.dependencies import get_db_session
from dera_api.db.models.identity import User, UserSession
from dera_api.db.models.workspace import Workspace, WorkspaceMembership
from dera_api.repositories.memberships import MembershipRepository
from dera_api.repositories.sessions import SessionRepository
from dera_api.repositories.workspaces import WorkspaceRepository


def _resolve_settings(request: Request):
    if (
        hasattr(request, "app")
        and hasattr(request.app, "state")
        and hasattr(request.app.state, "settings")
    ):
        return request.app.state.settings
    return get_settings()


def extract_session_token(request: Request) -> str | None:
    """Extract session token from Authorization header or session cookie."""
    settings = _resolve_settings(request)

    # 1. Prioritize Authorization header (Bearer token)
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()
        if token:
            return token

    # 2. Extract from ambient session cookie
    cookie_token = request.cookies.get(settings.auth_cookie_name)
    if cookie_token and cookie_token.strip():
        return cookie_token.strip()

    return None


async def get_optional_user_and_session(
    request: Request,
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
) -> tuple[User, UserSession] | None:
    """Resolve user and session if credentials are provided; return None if anonymous."""
    token = extract_session_token(request)
    if not token:
        return None

    token_hash = hash_session_token(token)
    session_repo = SessionRepository(db_session)
    user_session = await session_repo.get_by_token_hash(token_hash)

    if not user_session:
        return None

    # Check revocation
    if user_session.revoked_at is not None:
        raise SessionRevokedError()

    # Check expiration
    now = datetime.now(UTC)
    expires_at = user_session.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    if expires_at <= now:
        raise SessionExpiredError()

    # Check account status
    user = user_session.user
    if user.status != "active":
        raise AccountDisabledError()

    # Touch session activity
    await session_repo.touch_session(user_session)
    return user, user_session


async def get_current_user_and_session(
    user_and_session: Annotated[
        tuple[User, UserSession] | None,
        Depends(get_optional_user_and_session),
    ],
) -> tuple[User, UserSession]:
    """Require valid authenticated user and active session, raising 401 if unauthenticated."""
    if not user_and_session:
        raise AuthenticationRequiredError()
    return user_and_session


async def get_current_user(
    user_and_session: Annotated[
        tuple[User, UserSession],
        Depends(get_current_user_and_session),
    ],
) -> User:
    """Require authenticated user and return the User domain entity."""
    return user_and_session[0]


async def verify_csrf(request: Request) -> None:
    """Verify Double-Submit CSRF cookie & header on state-changing requests.

    Applies to state-changing methods (POST, PUT, PATCH, DELETE) when authentication
    relies on ambient session cookies.
    """
    settings = _resolve_settings(request)
    if not settings.auth_csrf_enabled:
        return

    # Safe read methods do not modify server state
    if request.method in {"GET", "HEAD", "OPTIONS"}:
        return

    # If authenticated via explicit Bearer header, CSRF is not applicable
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return

    # If authenticated via cookie, CSRF token validation is mandatory
    session_cookie = request.cookies.get(settings.auth_cookie_name)
    if session_cookie:
        csrf_cookie = request.cookies.get(settings.auth_csrf_cookie_name)
        csrf_header = request.headers.get(settings.auth_csrf_header_name)

        if not csrf_cookie or not csrf_header:
            raise CsrfValidationError()

        if not constant_time_compare(csrf_cookie, csrf_header):
            raise CsrfValidationError()


def require_workspace_permission(
    permission: Permission,
) -> Callable[..., tuple[Workspace, WorkspaceMembership]]:
    """Factory creating a FastAPI dependency that verifies workspace membership and permission.

    Resolves workspace by its URL slug, validates active user membership, and verifies
    role permission using default-deny evaluation.
    """

    async def _dependency(
        slug: str,
        current_user: Annotated[User, Depends(get_current_user)],
        db_session: Annotated[AsyncSession, Depends(get_db_session)],
    ) -> tuple[Workspace, WorkspaceMembership]:
        workspace_repo = WorkspaceRepository(db_session)
        workspace = await workspace_repo.get_by_slug(slug)
        if not workspace or workspace.status != "active":
            raise WorkspaceAccessDeniedError("Workspace does not exist or is inactive.")

        membership_repo = MembershipRepository(db_session)
        membership = await membership_repo.get_membership(workspace.id, current_user.id)
        if not membership or membership.status != "active":
            raise WorkspaceAccessDeniedError("You are not an active member of this workspace.")

        if not has_permission(membership.role, permission):
            raise PermissionDeniedError(
                f"Your role '{membership.role}' lacks the '{permission}' permission."
            )

        return workspace, membership

    return _dependency


def require_workspace_permission_by_id(
    permission: Permission,
) -> Callable[..., tuple[Workspace, WorkspaceMembership]]:
    """Factory creating a FastAPI dependency that verifies workspace membership and permission by workspace_id.

    Resolves workspace by its UUID identifier, validates active user membership, and verifies
    role permission using default-deny evaluation.
    """

    async def _dependency(
        workspace_id: uuid.UUID,
        current_user: Annotated[User, Depends(get_current_user)],
        db_session: Annotated[AsyncSession, Depends(get_db_session)],
    ) -> tuple[Workspace, WorkspaceMembership]:
        workspace_repo = WorkspaceRepository(db_session)
        workspace = await workspace_repo.get_by_id(workspace_id)
        if not workspace or workspace.status != "active":
            raise WorkspaceAccessDeniedError("Workspace does not exist or is inactive.")

        membership_repo = MembershipRepository(db_session)
        membership = await membership_repo.get_membership(workspace.id, current_user.id)
        if not membership or membership.status != "active":
            raise WorkspaceAccessDeniedError("You are not an active member of this workspace.")

        if not has_permission(membership.role, permission):
            raise PermissionDeniedError(
                f"Your role '{membership.role}' lacks the '{permission}' permission."
            )

        return workspace, membership

    return _dependency
