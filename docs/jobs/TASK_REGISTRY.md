# Task Registry & Whitelist

## Statically Registered Tasks

To prevent arbitrary remote code execution, DERA enforces an allowlist registry pattern (`TaskRegistry`). Workers will strictly refuse to execute any job type not registered in `default_task_registry`.

### Built-in Tasks (Phase 4.5)
1. **`system.health_probe.v1`**:
   - Performs a deterministic diagnostic health verification.
   - Input Payload: `{"target": str, "echo": Optional[str]}`
   - Result: `{"status": "ok", "worker_id": str, "timestamp": str}`
2. **`system.noop.v1`**:
   - A non-operational task used for concurrency qualification and synthetic load testing.
   - Input Payload: `{}`
   - Result: `{"status": "noop_completed"}`

## Registering New Tasks

Tasks must be registered with:
- `task_type`: Stable, versioned identifier string (e.g. `connectors.inspect_metadata.v1`).
- `handler`: Callable taking `(JobExecutionContext, dict[str, Any]) -> dict[str, Any]`.
- `schema`: Optional Pydantic model for payload validation.
- `default_timeout_seconds`: Bound on execution time.
- `retryable`: Boolean indicating whether transient failures trigger backoff retries.
