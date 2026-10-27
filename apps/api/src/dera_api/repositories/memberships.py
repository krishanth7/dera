"""DERA Repositories — Membership Repository.

Provides typed async database operations for workspace membership and role assignments.
"""

import uuid
from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from dera_api.db.models.workspace import WorkspaceMembership
from dera_api.repositories.base import BaseRepository


class MembershipRepository(BaseRepository[WorkspaceMembership]):
    """Repository managing user-to-workspace membership and roles."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, WorkspaceMembership)

    async def get_membership(
        self,
        workspace_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> WorkspaceMembership | None:
        """Retrieve membership record for a specific user in a workspace."""
        stmt = (
            select(WorkspaceMembership)
            .options(joinedload(WorkspaceMembership.user))
            .where(
                WorkspaceMembership.workspace_id == workspace_id,
                WorkspaceMembership.user_id == user_id,
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_memberships(
        self,
        workspace_id: uuid.UUID,
    ) -> Sequence[WorkspaceMembership]:
        """List all memberships in a workspace ordered by creation date."""
        stmt = (
            select(WorkspaceMembership)
            .options(joinedload(WorkspaceMembership.user))
            .where(WorkspaceMembership.workspace_id == workspace_id)
            .order_by(WorkspaceMembership.created_at.asc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def add_member(
        self,
        workspace_id: uuid.UUID,
        user_id: uuid.UUID,
        role: str = "viewer",
        status: str = "active",
    ) -> WorkspaceMembership:
        """Add a user to a workspace with a designated role."""
        now = datetime.now(UTC)
        membership = WorkspaceMembership(
            id=uuid.uuid4(),
            workspace_id=workspace_id,
            user_id=user_id,
            role=role.lower(),
            status=status,
            created_at=now,
            updated_at=now,
        )
        self.session.add(membership)
        await self.session.flush()
        return membership

    async def update_role(
        self,
        membership: WorkspaceMembership,
        new_role: str,
    ) -> WorkspaceMembership:
        """Update a member's role and refresh modification timestamp."""
        membership.role = new_role.lower()
        membership.updated_at = datetime.now(UTC)
        await self.session.flush()
        return membership

    async def remove_member(self, membership: WorkspaceMembership) -> None:
        """Remove a membership record from the workspace."""
        await self.session.delete(membership)
        await self.session.flush()

    async def count_active_owners(self, workspace_id: uuid.UUID) -> int:
        """Count active owner memberships in the workspace to safeguard against ownerless workspaces."""
        stmt = select(func.count(WorkspaceMembership.id)).where(
            WorkspaceMembership.workspace_id == workspace_id,
            WorkspaceMembership.role == "owner",
            WorkspaceMembership.status == "active",
        )
        result = await self.session.execute(stmt)
        return result.scalar_one() or 0
