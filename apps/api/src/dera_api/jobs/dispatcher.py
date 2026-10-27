"""DERA Jobs — Transactional Outbox Dispatcher.

Dispatches pending background job events from the PostgreSQL outbox to Celery / Redis.
Provides at-least-once delivery guarantees without message loss or orphan jobs.
"""

from __future__ import annotations

import logging
import uuid
from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import AsyncSession

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class JobOutboxDispatcher:
    """Dispatches durable transactional outbox records to the message broker."""

    def __init__(self, session: AsyncSession) -> None:
        from dera_api.repositories.jobs import JobOutboxRepository, JobRepository

        self.session = session
        self.outbox_repo = JobOutboxRepository(session)
        self.job_repo = JobRepository(session)

    async def dispatch_pending_events(self, limit: int = 50) -> int:
        """Poll and dispatch pending outbox events to Celery.

        Parameters
        ----------
        limit : int
            Maximum number of events to process in this batch.

        Returns
        -------
        int
            Number of successfully dispatched events.
        """
        events = await self.outbox_repo.get_pending_events(limit=limit)
        dispatched_count = 0

        for event in events:
            success = await self._dispatch_single_event(
                event_id=event.id,
                job_id=event.job_id,
                workspace_id=event.workspace_id,
            )
            if success:
                dispatched_count += 1

        return dispatched_count

    async def dispatch_single(
        self,
        event_id: uuid.UUID,
        job_id: uuid.UUID,
        workspace_id: uuid.UUID,
    ) -> bool:
        """Dispatch a single outbox record immediately following transaction commit."""
        return await self._dispatch_single_event(
            event_id=event_id,
            job_id=job_id,
            workspace_id=workspace_id,
        )

    async def _dispatch_single_event(
        self,
        event_id: uuid.UUID,
        job_id: uuid.UUID,
        workspace_id: uuid.UUID,
    ) -> bool:
        """Internal helper to publish a Celery task and update outbox & job states."""
        from dera_api.workers.tasks import execute_job_task

        try:
            # Publish to Celery broker
            execute_job_task.apply_async(
                args=[str(job_id), str(workspace_id)],
                queue="dera_jobs",
            )

            # Mark job status as QUEUED
            await self.job_repo.mark_queued(job_id)

            # Mark outbox event as DISPATCHED
            await self.outbox_repo.mark_dispatched(event_id)
            logger.info("Successfully dispatched job %s from outbox event %s.", job_id, event_id)
            return True

        except Exception as exc:
            logger.warning(
                "Failed to dispatch outbox event %s for job %s: %s. Will retry via outbox poller.",
                event_id,
                job_id,
                exc,
            )
            await self.outbox_repo.record_dispatch_failure(event_id)
            return False
