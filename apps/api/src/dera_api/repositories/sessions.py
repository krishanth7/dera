"""DERA Repositories — Session Repository.

Provides typed async database operations for server-managed user sessions.
"""

import uuid
from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from dera_api.db.models.identity import UserSession
from dera_api.repositories.base import BaseRepository


class SessionRepository(BaseRepository[UserSession]):
    """Repository managing user session persistence and token hash lookups."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, UserSession)

    async def create_session(
        self,
        user_id: uuid.UUID,
        token_hash: str,
        expires_at: datetime,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> UserSession:
        """Create and persist a new user session record."""
        now = datetime.now(UTC)
        user_session = UserSession(
            id=uuid.uuid4(),
            user_id=user_id,
            token_hash=token_hash,
            ip_address=ip_address,
            user_agent=user_agent[:255] if user_agent else None,
            expires_at=expires_at,
            revoked_at=None,
            created_at=now,
            last_seen_at=now,
        )
        self.session.add(user_session)
        await self.session.flush()
        return user_session

    async def get_by_token_hash(self, token_hash: str) -> UserSession | None:
        """Retrieve a session by its token hash, eagerly joining the associated user."""
        stmt = (
            select(UserSession)
            .options(joinedload(UserSession.user))
            .where(UserSession.token_hash == token_hash)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def touch_session(self, user_session: UserSession) -> None:
        """Update last_seen_at timestamp on the active session."""
        user_session.last_seen_at = datetime.now(UTC)
        await self.session.flush()

    async def revoke_session(self, user_session: UserSession) -> None:
        """Mark an individual session as revoked."""
        user_session.revoked_at = datetime.now(UTC)
        await self.session.flush()

    async def revoke_all_user_sessions(self, user_id: uuid.UUID) -> int:
        """Revoke all active sessions for a user (e.g., security reset / logout all)."""
        now = datetime.now(UTC)
        stmt = (
            update(UserSession)
            .where(
                UserSession.user_id == user_id,
                UserSession.revoked_at.is_(None),
            )
            .values(revoked_at=now)
            .execution_options(synchronize_session=False)
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount  # type: ignore[no-any-return]

    async def list_active_sessions(self, user_id: uuid.UUID) -> Sequence[UserSession]:
        """List all active non-revoked, non-expired sessions for a user."""
        now = datetime.now(UTC)
        stmt = (
            select(UserSession)
            .where(
                UserSession.user_id == user_id,
                UserSession.revoked_at.is_(None),
                UserSession.expires_at > now,
            )
            .order_by(UserSession.last_seen_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
