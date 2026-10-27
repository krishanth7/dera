"""DERA API — Workspace & Membership Endpoints.

Provides multi-tenant workspace creation, tenant-isolated member management,
role elevation controls, and owner protection safeguards.
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from dera_api.auth.dependencies import (
    get_current_user,
    require_workspace_permission,
    verify_csrf,
)
from dera_api.auth.email import normalize_email
from dera_api.auth.policies import (
    PolicyViolationError,
    validate_owner_removal,
    validate_role_transition,
)
from dera_api.auth.roles import Permission, WorkspaceRole
from dera_api.contracts.errors import ProblemDetail
from dera_api.db.dependencies import get_db_session
from dera_api.db.models.identity import User
from dera_api.db.models.workspace import Workspace, WorkspaceMembership
from dera_api.db.session import transaction_scope
from dera_api.repositories.audit import AuditRepository
from dera_api.repositories.memberships import MembershipRepository
from dera_api.repositories.users import UserRepository
from dera_api.repositories.workspaces import WorkspaceRepository
from dera_api.schemas.workspaces import (
    AddMemberRequest,
    CreateWorkspaceRequest,
    MembershipResponse,
    UpdateMemberRoleRequest,
    WorkspaceResponse,
)

router = APIRouter(prefix="/workspaces", tags=["Workspaces"])


@router.post(
    "",
    response_model=WorkspaceResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(verify_csrf)],
    summary="Create a new multi-tenant workspace with caller as Owner",
    responses={
        400: {"model": ProblemDetail, "description": "Invalid workspace name or slug syntax"},
        401: {"model": ProblemDetail, "description": "Authentication required"},
        409: {"model": ProblemDetail, "description": "Workspace slug already in use"},
    },
)
async def create_workspace(
    request: Request,
    payload: CreateWorkspaceRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
) -> WorkspaceResponse:
    """Create a new tenant workspace and assign the creator the Owner role."""
    client_ip = request.client.host if request.client else None
    request_id = getattr(request.state, "request_id", None)

    async with transaction_scope(db_session):
        workspace_repo = WorkspaceRepository(db_session)
        audit_repo = AuditRepository(db_session)

        # Check slug uniqueness
        existing = await workspace_repo.get_by_slug(payload.slug)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Workspace with slug '{payload.slug}' already exists.",
            )

        workspace, membership = await workspace_repo.create_workspace(
            name=payload.name,
            slug=payload.slug,
            owner_user_id=current_user.id,
        )

        await audit_repo.record_event(
            event_type="workspace.create.success",
            actor_user_id=current_user.id,
            workspace_id=workspace.id,
            target_type="workspace",
            target_id=str(workspace.id),
            request_id=request_id,
            ip_address=client_ip,
        )

    return WorkspaceResponse(
        id=workspace.id,
        name=workspace.name,
        slug=workspace.slug,
        status=workspace.status,
        created_at=workspace.created_at,
        updated_at=workspace.updated_at,
        current_user_role=membership.role,
    )


@router.get(
    "",
    response_model=list[WorkspaceResponse],
    summary="List all workspaces accessible to the authenticated user",
    responses={
        401: {"model": ProblemDetail, "description": "Authentication required"},
    },
)
async def list_workspaces(
    current_user: Annotated[User, Depends(get_current_user)],
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[WorkspaceResponse]:
    """Return all workspaces where the current user maintains an active membership."""
    workspace_repo = WorkspaceRepository(db_session)
    results = await workspace_repo.list_for_user(current_user.id)

    return [
        WorkspaceResponse(
            id=ws.id,
            name=ws.name,
            slug=ws.slug,
            status=ws.status,
            created_at=ws.created_at,
            updated_at=ws.updated_at,
            current_user_role=mb.role,
        )
        for ws, mb in results
    ]


@router.get(
    "/{slug}",
    response_model=WorkspaceResponse,
    summary="Get workspace details scoped by tenant slug",
    responses={
        401: {"model": ProblemDetail, "description": "Authentication required"},
        403: {"model": ProblemDetail, "description": "Workspace access denied"},
    },
)
async def get_workspace(
    workspace_and_membership: Annotated[
        tuple[Workspace, WorkspaceMembership],
        Depends(require_workspace_permission(Permission.WORKSPACE_READ)),
    ],
) -> WorkspaceResponse:
    """Retrieve details for a single workspace requiring active membership."""
    workspace, membership = workspace_and_membership
    return WorkspaceResponse(
        id=workspace.id,
        name=workspace.name,
        slug=workspace.slug,
        status=workspace.status,
        created_at=workspace.created_at,
        updated_at=workspace.updated_at,
        current_user_role=membership.role,
    )


@router.get(
    "/{slug}/members",
    response_model=list[MembershipResponse],
    summary="List all members of a workspace",
    responses={
        401: {"model": ProblemDetail, "description": "Authentication required"},
        403: {"model": ProblemDetail, "description": "Workspace access denied"},
    },
)
async def list_members(
    workspace_and_membership: Annotated[
        tuple[Workspace, WorkspaceMembership],
        Depends(require_workspace_permission(Permission.MEMBER_READ)),
    ],
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[MembershipResponse]:
    """List all user memberships and roles within the workspace boundary."""
    workspace, _ = workspace_and_membership
    membership_repo = MembershipRepository(db_session)
    memberships = await membership_repo.list_memberships(workspace.id)

    return [
        MembershipResponse(
            id=m.id,
            workspace_id=m.workspace_id,
            user_id=m.user_id,
            user_email=m.user.email if m.user else None,
            role=m.role,
            status=m.status,
            created_at=m.created_at,
            updated_at=m.updated_at,
        )
        for m in memberships
    ]


@router.post(
    "/{slug}/members",
    response_model=MembershipResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(verify_csrf)],
    summary="Add a user to the workspace with a designated role",
    responses={
        400: {"model": ProblemDetail, "description": "Invalid role or policy violation"},
        401: {"model": ProblemDetail, "description": "Authentication required"},
        403: {"model": ProblemDetail, "description": "Permission denied"},
        404: {"model": ProblemDetail, "description": "User email not found"},
        409: {"model": ProblemDetail, "description": "User is already a member of this workspace"},
    },
)
async def add_member(
    request: Request,
    payload: AddMemberRequest,
    workspace_and_membership: Annotated[
        tuple[Workspace, WorkspaceMembership],
        Depends(require_workspace_permission(Permission.MEMBER_INVITE)),
    ],
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
) -> MembershipResponse:
    """Add an existing user to the workspace while validating role escalation boundaries."""
    workspace, actor_membership = workspace_and_membership
    client_ip = request.client.host if request.client else None
    request_id = getattr(request.state, "request_id", None)
    clean_email = normalize_email(payload.email)

    try:
        actor_role = WorkspaceRole(actor_membership.role)
        target_role = WorkspaceRole(payload.role)
        validate_role_transition(actor_role, WorkspaceRole.VIEWER, target_role)
    except (ValueError, PolicyViolationError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    async with transaction_scope(db_session):
        user_repo = UserRepository(db_session)
        membership_repo = MembershipRepository(db_session)
        audit_repo = AuditRepository(db_session)

        target_user = await user_repo.get_by_email(clean_email)
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with email '{clean_email}' was not found.",
            )

        existing_mb = await membership_repo.get_membership(workspace.id, target_user.id)
        if existing_mb:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"User '{clean_email}' is already a member of this workspace.",
            )

        new_membership = await membership_repo.add_member(
            workspace_id=workspace.id,
            user_id=target_user.id,
            role=target_role.value,
            status="active",
        )

        await audit_repo.record_event(
            event_type="member.add.success",
            actor_user_id=actor_membership.user_id,
            workspace_id=workspace.id,
            target_type="membership",
            target_id=str(new_membership.id),
            request_id=request_id,
            ip_address=client_ip,
            metadata={"assigned_role": target_role.value, "target_user_id": str(target_user.id)},
        )

    return MembershipResponse(
        id=new_membership.id,
        workspace_id=new_membership.workspace_id,
        user_id=new_membership.user_id,
        user_email=target_user.email,
        role=new_membership.role,
        status=new_membership.status,
        created_at=new_membership.created_at,
        updated_at=new_membership.updated_at,
    )


@router.patch(
    "/{slug}/members/{user_id}",
    response_model=MembershipResponse,
    dependencies=[Depends(verify_csrf)],
    summary="Update a workspace member's role",
    responses={
        400: {"model": ProblemDetail, "description": "Invalid role transition or owner safeguard"},
        401: {"model": ProblemDetail, "description": "Authentication required"},
        403: {"model": ProblemDetail, "description": "Permission denied"},
        404: {"model": ProblemDetail, "description": "Member not found"},
    },
)
async def update_member_role(
    request: Request,
    user_id: uuid.UUID,
    payload: UpdateMemberRoleRequest,
    workspace_and_membership: Annotated[
        tuple[Workspace, WorkspaceMembership],
        Depends(require_workspace_permission(Permission.MEMBER_UPDATE_ROLE)),
    ],
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
) -> MembershipResponse:
    """Modify a member's role, verifying administrative hierarchy and owner safeguards."""
    workspace, actor_membership = workspace_and_membership
    client_ip = request.client.host if request.client else None
    request_id = getattr(request.state, "request_id", None)

    async with transaction_scope(db_session):
        membership_repo = MembershipRepository(db_session)
        audit_repo = AuditRepository(db_session)

        target_mb = await membership_repo.get_membership(workspace.id, user_id)
        if not target_mb:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workspace member was not found.",
            )

        try:
            actor_role = WorkspaceRole(actor_membership.role)
            current_role = WorkspaceRole(target_mb.role)
            new_role = WorkspaceRole(payload.role)

            # Prevent demoting the last remaining active owner
            if current_role == WorkspaceRole.OWNER and new_role != WorkspaceRole.OWNER:
                active_owners = await membership_repo.count_active_owners(workspace.id)
                validate_owner_removal(active_owners)

            validate_role_transition(actor_role, current_role, new_role)
        except (ValueError, PolicyViolationError) as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

        updated_mb = await membership_repo.update_role(target_mb, new_role.value)

        await audit_repo.record_event(
            event_type="member.role.update",
            actor_user_id=actor_membership.user_id,
            workspace_id=workspace.id,
            target_type="membership",
            target_id=str(updated_mb.id),
            request_id=request_id,
            ip_address=client_ip,
            metadata={"previous_role": current_role.value, "new_role": new_role.value},
        )

    return MembershipResponse(
        id=updated_mb.id,
        workspace_id=updated_mb.workspace_id,
        user_id=updated_mb.user_id,
        user_email=updated_mb.user.email if updated_mb.user else None,
        role=updated_mb.role,
        status=updated_mb.status,
        created_at=updated_mb.created_at,
        updated_at=updated_mb.updated_at,
    )


@router.delete(
    "/{slug}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(verify_csrf)],
    summary="Remove a member from the workspace",
    responses={
        400: {"model": ProblemDetail, "description": "Cannot remove the last owner"},
        401: {"model": ProblemDetail, "description": "Authentication required"},
        403: {"model": ProblemDetail, "description": "Permission denied"},
        404: {"model": ProblemDetail, "description": "Member not found"},
    },
)
async def remove_member(
    request: Request,
    user_id: uuid.UUID,
    workspace_and_membership: Annotated[
        tuple[Workspace, WorkspaceMembership],
        Depends(require_workspace_permission(Permission.MEMBER_REMOVE)),
    ],
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
) -> None:
    """Remove a user from a workspace while preventing ownerless workspaces."""
    workspace, actor_membership = workspace_and_membership
    client_ip = request.client.host if request.client else None
    request_id = getattr(request.state, "request_id", None)

    async with transaction_scope(db_session):
        membership_repo = MembershipRepository(db_session)
        audit_repo = AuditRepository(db_session)

        target_mb = await membership_repo.get_membership(workspace.id, user_id)
        if not target_mb:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workspace member was not found.",
            )

        # Safeguard: cannot remove last owner
        if target_mb.role == "owner":
            active_owners = await membership_repo.count_active_owners(workspace.id)
            try:
                validate_owner_removal(active_owners)
            except PolicyViolationError as exc:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
                ) from exc

        # Only an OWNER can remove another OWNER
        if target_mb.role == "owner" and actor_membership.role != "owner":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only workspace owners can remove another owner.",
            )

        await membership_repo.remove_member(target_mb)

        await audit_repo.record_event(
            event_type="member.remove.success",
            actor_user_id=actor_membership.user_id,
            workspace_id=workspace.id,
            target_type="membership",
            target_id=str(target_mb.id),
            request_id=request_id,
            ip_address=client_ip,
            metadata={"removed_user_id": str(user_id)},
        )
