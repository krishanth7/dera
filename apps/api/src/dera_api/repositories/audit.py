"""DERA Repositories — Audit Event Repository.

Provides typed async database operations for recording and querying security audit events.
"""

import json
import uuid
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from dera_api.db.models.audit import SecurityAuditEvent
from dera_api.repositories.base import BaseRepository


class AuditRepository(BaseRepository[SecurityAuditEvent]):
    """Repository managing security audit event persistence."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, SecurityAuditEvent)

    async def record_event(
        self,
        event_type: str,
        actor_user_id: uuid.UUID | None = None,
        workspace_id: uuid.UUID | None = None,
        target_type: str | None = None,
        target_id: str | None = None,
        request_id: str | None = None,
        ip_address: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> SecurityAuditEvent:
        """Record an immutable security audit event."""
        metadata_str = json.dumps(metadata) if metadata else None
        event = SecurityAuditEvent(
            id=uuid.uuid4(),
            event_type=event_type,
            actor_user_id=actor_user_id,
            workspace_id=workspace_id,
            target_type=target_type,
            target_id=target_id,
            request_id=request_id,
            ip_address=ip_address,
            metadata_json=metadata_str,
            created_at=datetime.now(UTC),
        )
        self.session.add(event)
        await self.session.flush()
        return event

    async def list_events_for_workspace(
        self,
        workspace_id: uuid.UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> Sequence[SecurityAuditEvent]:
        """List audit events for a specific workspace ordered by timestamp descending."""
        stmt = (
            select(SecurityAuditEvent)
            .where(SecurityAuditEvent.workspace_id == workspace_id)
            .order_by(SecurityAuditEvent.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
