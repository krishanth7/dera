"""DERA Repositories — User Repository.

Provides typed async database operations for user accounts bound to an explicit AsyncSession.
"""

import uuid
from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from dera_api.db.models.identity import User
from dera_api.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository managing user account persistence."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, User)

    async def create(
        self,
        email: str,
        password_hash: str,
        status: str = "active",
        email_verified_at: datetime | None = None,
    ) -> User:
        """Create and persist a new user entity."""
        user = User(
            id=uuid.uuid4(),
            email=email,
            password_hash=password_hash,
            status=status,
            email_verified_at=email_verified_at,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        self.session.add(user)
        await self.session.flush()
        return user

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        """Retrieve a user by their unique UUID identifier."""
        stmt = select(User).where(User.id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        """Retrieve a user by their unique normalized email address."""
        stmt = select(User).where(User.email == email)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_users(self, limit: int = 50, offset: int = 0) -> Sequence[User]:
        """List users ordered by creation date."""
        stmt = select(User).order_by(User.created_at.desc()).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return result.scalars().all()
