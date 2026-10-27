"""Reliability and Failure Recovery Tests.

Validates:
- Transactional outbox persistence and dispatch retry on broker disconnect.
- Atomic compare-and-swap job claiming preventing concurrent worker races.
- Safe handling of duplicate message delivery.
"""

import unittest
import uuid
from unittest.mock import patch

from dera_api.core.config import ApiSettings
from dera_api.db.base import Base
from dera_api.db.engine import create_database_engine, dispose_database_engine
from dera_api.db.models.workspace import Workspace
from dera_api.db.session import create_session_factory, transaction_scope
from dera_api.jobs.dispatcher import JobOutboxDispatcher
from dera_api.jobs.enums import OutboxEventStatus
from dera_api.repositories.jobs import JobOutboxRepository, JobRepository
from dera_api.workers.tasks import execute_job_async


class TestCrashRecovery(unittest.IsolatedAsyncioTestCase):
    """Test suite validating failure recovery, outbox reliability, and race condition defenses."""

    async def asyncSetUp(self) -> None:
        self.settings = ApiSettings(
            environment="testing",
            database_url="sqlite+aiosqlite:///:memory:",
            job_default_timeout_seconds=30,
        )
        self.engine = create_database_engine(self.settings)

        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        self.session_factory = create_session_factory(self.engine)

        self.workspace_id = uuid.uuid4()
        async with self.session_factory() as session, transaction_scope(session):
            ws = Workspace(
                id=self.workspace_id,
                name="Reliability Workspace",
                slug="reliability-ws",
                status="active",
            )
            session.add(ws)

    async def asyncTearDown(self) -> None:
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await dispose_database_engine(self.engine)

    async def test_outbox_retry_on_broker_failure(self) -> None:
        """Verify outbox retains pending state when broker dispatch fails, then succeeds on retry."""
        async with self.session_factory() as session, transaction_scope(session):
            job_repo = JobRepository(session)
            outbox_repo = JobOutboxRepository(session)

            job = await job_repo.create_job(
                workspace_id=self.workspace_id,
                job_type="system.health_probe.v1",
                payload={},
            )
            await outbox_repo.create_event(
                job_id=job.id,
                workspace_id=self.workspace_id,
            )

        # 1. Simulate broker failure during dispatch
        async with self.session_factory() as session, transaction_scope(session):
            dispatcher = JobOutboxDispatcher(session)

            with patch(
                "dera_api.workers.tasks.execute_job_task.apply_async",
                side_effect=ConnectionError("Redis down"),
            ):
                dispatched = await dispatcher.dispatch_pending_events()
                self.assertEqual(dispatched, 0)

        # Verify event remains PENDING and retry_count was incremented
        async with self.session_factory() as session:
            outbox_repo = JobOutboxRepository(session)
            events = await outbox_repo.get_pending_events()
            self.assertEqual(len(events), 1)
            self.assertEqual(events[0].status, OutboxEventStatus.PENDING.value)
            self.assertEqual(events[0].retry_count, 1)

        # 2. Broker recovers: subsequent dispatch succeeds
        async with self.session_factory() as session, transaction_scope(session):
            dispatcher = JobOutboxDispatcher(session)
            with patch("dera_api.workers.tasks.execute_job_task.apply_async") as mock_publish:
                dispatched = await dispatcher.dispatch_pending_events()
                self.assertEqual(dispatched, 1)
                mock_publish.assert_called_once()

        # Verify event is now DISPATCHED
        async with self.session_factory() as session:
            outbox_repo = JobOutboxRepository(session)
            events = await outbox_repo.get_pending_events()
            self.assertEqual(len(events), 0)

    async def test_concurrent_worker_claim_race_defense(self) -> None:
        """Verify atomic compare-and-swap prevents two workers from claiming the same job."""
        async with self.session_factory() as session, transaction_scope(session):
            repo = JobRepository(session)
            job = await repo.create_job(
                workspace_id=self.workspace_id,
                job_type="system.health_probe.v1",
                payload={},
            )
            await repo.mark_queued(job.id)

        # Worker 1 claims job
        claim_1_outcome = await execute_job_async(
            job_id=job.id,
            workspace_id=self.workspace_id,
            worker_id="worker-one",
            session_factory=self.session_factory,
        )
        self.assertEqual(claim_1_outcome["status"], "succeeded")

        # Worker 2 attempts to claim same job simultaneously or immediately after
        claim_2_outcome = await execute_job_async(
            job_id=job.id,
            workspace_id=self.workspace_id,
            worker_id="worker-two",
            session_factory=self.session_factory,
        )
        self.assertEqual(claim_2_outcome["status"], "claim_failed")

        # Verify attempt_count was only incremented once by Worker 1
        async with self.session_factory() as session:
            repo = JobRepository(session)
            persisted = await repo.get_by_id(self.workspace_id, job.id)
            self.assertIsNotNone(persisted)
            self.assertEqual(persisted.attempt_count, 1)
            self.assertEqual(persisted.worker_id, "worker-one")


if __name__ == "__main__":
    unittest.main()
