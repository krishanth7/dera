"""DERA Jobs — Allowlisted Task Registry.

Enforces strict allowlisting of background task types. Prohibits arbitrary code execution,
dynamic deserialization, and unvalidated payloads.
"""

from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field, ValidationError

from dera_api.jobs.exceptions import JobPayloadInvalidError, JobTypeUnsupportedError
from dera_api.jobs.schemas import JobExecutionContext


class TaskDefinition:
    """Metadata and execution contract for an allowlisted task."""

    def __init__(
        self,
        task_type: str,
        handler: Callable[[JobExecutionContext, dict[str, Any]], dict[str, Any]],
        payload_schema: type[BaseModel] | None = None,
        description: str = "",
    ) -> None:
        self.task_type = task_type
        self.handler = handler
        self.payload_schema = payload_schema
        self.description = description

    def validate_payload(self, raw_payload: dict[str, Any]) -> dict[str, Any]:
        """Validate raw input payload against the typed Pydantic schema."""
        if self.payload_schema is None:
            return raw_payload

        try:
            parsed = self.payload_schema.model_validate(raw_payload)
            return parsed.model_dump()
        except ValidationError as exc:
            raise JobPayloadInvalidError(str(exc)) from exc


class TaskRegistry:
    """Allowlist registry for background task handlers."""

    def __init__(self) -> None:
        self._tasks: dict[str, TaskDefinition] = {}

    def register(
        self,
        task_type: str,
        handler: Callable[[JobExecutionContext, dict[str, Any]], dict[str, Any]],
        payload_schema: type[BaseModel] | None = None,
        description: str = "",
    ) -> None:
        """Register a new deterministic task handler."""
        self._tasks[task_type] = TaskDefinition(
            task_type=task_type,
            handler=handler,
            payload_schema=payload_schema,
            description=description,
        )

    def get(self, task_type: str) -> TaskDefinition:
        """Look up a task definition by its type name.

        Raises
        ------
        JobTypeUnsupportedError
            If the task type has not been explicitly allowlisted.
        """
        task = self._tasks.get(task_type)
        if task is None:
            raise JobTypeUnsupportedError(task_type)
        return task

    def is_registered(self, task_type: str) -> bool:
        """Check if a task type is allowlisted."""
        return task_type in self._tasks

    def list_task_types(self) -> list[str]:
        """Return all registered task type identifiers."""
        return sorted(self._tasks.keys())


# --- Baseline System Tasks ---


class HealthProbePayload(BaseModel):
    """Schema for system health probe background tasks."""

    target: str = Field(
        default="system",
        max_length=64,
        description="Target component or system to probe.",
    )


def handle_health_probe(
    ctx: JobExecutionContext,
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Execute a deterministic health probe task verifying background processing."""
    target = payload.get("target", "system")
    return {
        "status": "healthy",
        "target": target,
        "job_id": str(ctx.job_id),
        "workspace_id": str(ctx.workspace_id),
        "attempt": ctx.attempt_number,
        "executed_at": datetime.now(UTC).isoformat(),
        "worker_id": ctx.worker_id,
    }


class NoopPayload(BaseModel):
    """Schema for test no-op background tasks."""

    echo: str | None = Field(default=None, max_length=256)


def handle_noop(
    ctx: JobExecutionContext,
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Execute a no-op task used for throughput and baseline latency benchmarks."""
    return {
        "status": "completed",
        "echo": payload.get("echo"),
        "job_id": str(ctx.job_id),
        "executed_at": datetime.now(UTC).isoformat(),
    }


# Global authoritative task registry
default_task_registry = TaskRegistry()

# Register core baseline tasks
default_task_registry.register(
    task_type="system.health_probe.v1",
    handler=handle_health_probe,
    payload_schema=HealthProbePayload,
    description="Deterministic background health probe verifying end-to-end task execution.",
)

default_task_registry.register(
    task_type="system.noop.v1",
    handler=handle_noop,
    payload_schema=NoopPayload,
    description="Deterministic no-op background task for testing and benchmarking.",
)
