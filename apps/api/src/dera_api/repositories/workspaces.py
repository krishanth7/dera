"""DERA Repositories — Workspace Repository.

Provides typed async database operations for multi-tenant workspace management.
"""

import uuid
from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from dera_api.db.models.workspace import Workspace, WorkspaceMembership
from dera_api.repositories.base import BaseRepository


class WorkspaceRepository(BaseRepository[Workspace]):
    """Repository managing workspace entity persistence and lookups."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Workspace)

    async def create_workspace(
        self,
        name: str,
        slug: str,
        owner_user_id: uuid.UUID,
        status: str = "active",
    ) -> tuple[Workspace, WorkspaceMembership]:
        """Create a new workspace and automatically establish the creator as the Owner.

        Executed atomically within the current transaction scope.
        """
        now = datetime.now(UTC)
        workspace = Workspace(
            id=uuid.uuid4(),
            name=name,
            slug=slug,
            status=status,
            created_at=now,
            updated_at=now,
        )
        self.session.add(workspace)
        await self.session.flush()

        # Add initial owner membership
        membership = WorkspaceMembership(
            id=uuid.uuid4(),
            workspace_id=workspace.id,
            user_id=owner_user_id,
            role="owner",
            status="active",
            created_at=now,
            updated_at=now,
        )
        self.session.add(membership)
        await self.session.flush()

        return workspace, membership

    async def get_by_id(self, workspace_id: uuid.UUID) -> Workspace | None:
        """Retrieve a workspace by its unique UUID identifier."""
        stmt = select(Workspace).where(Workspace.id == workspace_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Workspace | None:
        """Retrieve a workspace by its unique URL-safe slug."""
        stmt = select(Workspace).where(Workspace.slug == slug)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_for_user(
        self,
        user_id: uuid.UUID,
    ) -> Sequence[tuple[Workspace, WorkspaceMembership]]:
        """List all active workspaces where the specified user has an active membership."""
        stmt = (
            select(Workspace, WorkspaceMembership)
            .join(
                WorkspaceMembership,
                WorkspaceMembership.workspace_id == Workspace.id,
            )
            .where(
                WorkspaceMembership.user_id == user_id,
                WorkspaceMembership.status == "active",
                Workspace.status == "active",
            )
            .order_by(Workspace.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.all()  # type: ignore[return-value]
