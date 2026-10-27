"""Unit Tests for Background Task Registry.

Validates that task allowlisting, typed payload schemas, and baseline system
tasks operate deterministically and reject untrusted or malformed inputs.
"""

import unittest
import uuid
from typing import Any

from dera_api.jobs.exceptions import JobPayloadInvalidError, JobTypeUnsupportedError
from dera_api.jobs.registry import TaskRegistry, default_task_registry
from dera_api.jobs.schemas import JobExecutionContext
from pydantic import BaseModel, Field


class CustomSamplePayload(BaseModel):
    """Test payload schema."""

    name: str = Field(min_length=2, max_length=50)
    count: int = Field(ge=1, le=10)


class TestTaskRegistry(unittest.TestCase):
    """Test suite validating task allowlist registration and payload validation."""

    def test_default_system_tasks_registered(self) -> None:
        """Verify baseline system tasks exist in the default registry."""
        task_types = default_task_registry.list_task_types()
        self.assertIn("system.health_probe.v1", task_types)
        self.assertIn("system.noop.v1", task_types)

    def test_unsupported_task_raises_error(self) -> None:
        """Verify querying an unallowlisted task raises JobTypeUnsupportedError."""
        with self.assertRaises(JobTypeUnsupportedError) as ctx:
            default_task_registry.get("system.untrusted_script.v1")
        self.assertEqual(ctx.exception.job_type, "system.untrusted_script.v1")

    def test_custom_task_registration_and_validation(self) -> None:
        """Verify registering a custom task validates payloads correctly."""
        registry = TaskRegistry()

        def dummy_handler(ctx: JobExecutionContext, payload: dict[str, Any]) -> dict[str, Any]:
            return {"echo_name": payload["name"], "echo_count": payload["count"]}

        registry.register(
            task_type="custom.sample.v1",
            handler=dummy_handler,
            payload_schema=CustomSamplePayload,
            description="Sample test task",
        )

        self.assertTrue(registry.is_registered("custom.sample.v1"))
        task_def = registry.get("custom.sample.v1")

        # Valid payload
        validated = task_def.validate_payload({"name": "Analysis", "count": 5})
        self.assertEqual(validated["name"], "Analysis")
        self.assertEqual(validated["count"], 5)

        # Invalid payload: count out of bounds
        with self.assertRaises(JobPayloadInvalidError):
            task_def.validate_payload({"name": "Analysis", "count": 999})

        # Invalid payload: name too short
        with self.assertRaises(JobPayloadInvalidError):
            task_def.validate_payload({"name": "A", "count": 5})

    def test_health_probe_handler_execution(self) -> None:
        """Verify execution of the built-in system.health_probe.v1 task."""
        task_def = default_task_registry.get("system.health_probe.v1")
        ctx = JobExecutionContext(
            job_id=uuid.uuid4(),
            workspace_id=uuid.uuid4(),
            job_type="system.health_probe.v1",
            attempt_number=1,
            timeout_seconds=30,
            worker_id="test-worker-1",
        )

        payload = task_def.validate_payload({"target": "database"})
        result = task_def.handler(ctx, payload)

        self.assertEqual(result["status"], "healthy")
        self.assertEqual(result["target"], "database")
        self.assertEqual(result["job_id"], str(ctx.job_id))
        self.assertEqual(result["worker_id"], "test-worker-1")

    def test_noop_handler_execution(self) -> None:
        """Verify execution of the built-in system.noop.v1 task."""
        task_def = default_task_registry.get("system.noop.v1")
        ctx = JobExecutionContext(
            job_id=uuid.uuid4(),
            workspace_id=uuid.uuid4(),
            job_type="system.noop.v1",
            attempt_number=1,
            timeout_seconds=30,
            worker_id="test-worker-1",
        )

        payload = task_def.validate_payload({"echo": "ping"})
        result = task_def.handler(ctx, payload)

        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["echo"], "ping")


if __name__ == "__main__":
    unittest.main()
