"""Integration Tests for Background Worker Execution.

Validates atomic job claiming, execution of allowlisted tasks, result persistence,
timeout handling, error classification, and retry scheduling.
"""

from collections.abc import AsyncIterator
import unittest
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from dera_api.core.config import ApiSettings
from dera_api.db.base import Base
from dera_api.db.engine import create_database_engine, dispose_database_engine
from dera_api.db.models.workspace import Workspace
from dera_api.db.session import create_session_factory, transaction_scope
from dera_api.jobs.enums import JobPriority, JobStatus
from dera_api.jobs.registry import default_task_registry
from dera_api.jobs.schemas import JobCreateRequest
from dera_api.jobs.service import JobService
from dera_api.repositories.jobs import JobRepository
from dera_api.workers.health import get_worker_status
from dera_api.workers.tasks import execute_job_async


class TestWorkerExecution(unittest.IsolatedAsyncioTestCase):
    """Test suite validating worker task execution and lifecycle state changes."""

    async def asyncSetUp(self) -> None:
        self.settings = ApiSettings(
            database_url="sqlite+aiosqlite:///:memory:",
            job_default_timeout_seconds=30,
            job_max_attempts=3,
        )
        self.engine = create_database_engine(self.settings)

        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        self.session_factory = create_session_factory(self.engine)

        self.workspace_id = uuid.uuid4()
        async with self.session_factory() as session, transaction_scope(session):
            ws = Workspace(
                id=self.workspace_id,
                name="Worker Execution Workspace",
                slug="worker-exec-ws",
                status="active",
            )
            session.add(ws)

    async def asyncTearDown(self) -> None:
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await dispose_database_engine(self.engine)

    async def test_worker_execute_health_probe_success(self) -> None:
        """Verify worker successfully claims, executes, and records result for health probe."""
        req = JobCreateRequest(
            job_type="system.health_probe.v1",
            payload={"target": "worker_test"},
        )

        async with self.session_factory() as session, transaction_scope(session):
            service = JobService(session)
            job = await service.submit_job(self.workspace_id, req)
            # Ensure job is marked QUEUED so worker can claim it
            repo = JobRepository(session)
            await repo.mark_queued(job.id)

        # Worker executes job
        outcome = await execute_job_async(
            job_id=job.id,
            workspace_id=self.workspace_id,
            worker_id="test-worker-alpha",
            session_factory=self.session_factory,
        )

        self.assertEqual(outcome["status"], "succeeded")

        # Verify persisted state in database
        async with self.session_factory() as session:
            repo = JobRepository(session)
            persisted = await repo.get_by_id(self.workspace_id, job.id)
            self.assertIsNotNone(persisted)
            self.assertEqual(persisted.status, JobStatus.SUCCEEDED.value)
            self.assertEqual(persisted.attempt_count, 1)
            self.assertEqual(persisted.worker_id, "test-worker-alpha")
            self.assertIsNotNone(persisted.result)
            self.assertEqual(persisted.result["target"], "worker_test")
            self.assertIsNotNone(persisted.finished_at)

    async def test_worker_claim_fails_if_not_queued(self) -> None:
        """Verify worker cannot claim a job that is still PENDING or already terminal."""
        req = JobCreateRequest(job_type="system.health_probe.v1", payload={})

        async with self.session_factory() as session, transaction_scope(session):
            service = JobService(session)
            job = await service.submit_job(self.workspace_id, req)
            # Job is in PENDING status, not yet QUEUED

        outcome = await execute_job_async(
            job_id=job.id,
            workspace_id=self.workspace_id,
            worker_id="test-worker-beta",
            session_factory=self.session_factory,
        )

        self.assertEqual(outcome["status"], "claim_failed")

    async def test_worker_handles_task_timeout(self) -> None:
        """Verify worker records JOB_TIMEOUT when task execution exceeds deadline."""
        # Register a slow task
        def slow_handler(ctx: Any, payload: dict[str, Any]) -> dict[str, Any]:
            import time
            time.sleep(1.0)
            return {"done": True}

        default_task_registry.register(
            task_type="test.slow_task.v1",
            handler=slow_handler,
        )

        # Create job with 0-second (or very small) timeout
        async with self.session_factory() as session, transaction_scope(session):
            repo = JobRepository(session)
            job = await repo.create_job(
                workspace_id=self.workspace_id,
                job_type="test.slow_task.v1",
                payload={},
                timeout_seconds=0,  # Forces timeout immediately
            )
            await repo.mark_queued(job.id)

        outcome = await execute_job_async(
            job_id=job.id,
            workspace_id=self.workspace_id,
            worker_id="test-worker-timeout",
            session_factory=self.session_factory,
        )

        self.assertEqual(outcome["status"], "timeout")

        # Verify job recorded failure
        async with self.session_factory() as session:
            repo = JobRepository(session)
            persisted = await repo.get_by_id(self.workspace_id, job.id)
            self.assertIsNotNone(persisted)
            self.assertEqual(persisted.error_code, "JOB_TIMEOUT")

    def test_worker_status_diagnostics(self) -> None:
        """Verify worker diagnostics return registered tasks and queue info."""
        status = get_worker_status()
        self.assertEqual(status["status"], "ready")
        self.assertGreaterEqual(status["task_count"], 2)
        self.assertIn("system.health_probe.v1", status["registered_tasks"])


if __name__ == "__main__":
    unittest.main()
