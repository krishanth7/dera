# DERA Background Jobs & Asynchronous Orchestration Subsystem

## Overview

The DERA Background Jobs & Asynchronous Orchestration subsystem (Phase 4.5) provides reliable, deterministic, tenant-isolated background task execution for the DERA platform. It pairs PostgreSQL durable persistence (via `dera_jobs` and `dera_job_outbox`) with Celery/Redis for message distribution and cooperative worker execution.

## Core Invariants

1. **Deterministic Execution:** No AI/LLM models, dynamic prompts, or stochastic decision-making in background processing.
2. **Tenant Isolation:** Every job, outbox event, and execution payload is bound to a workspace (`workspace_id`). Cross-tenant execution or access is strictly rejected.
3. **At-Least-Once Delivery via Transactional Outbox:** Job creation and outbox scheduling occur in a single atomic database transaction. Celery dispatches from the outbox; broker crashes cannot cause orphan jobs or missing records.
4. **Strict Task Allowlist:** Only statically registered, strongly typed task definitions in `default_task_registry` can be invoked. Arbitrary code execution is impossible.
5. **Least Privilege & Safe Serialization:** Serialization is restricted to strict JSON (`accept_content=["json"]`). Pickle deserialization is completely prohibited.

## Directory Structure

```
apps/api/src/dera_api/jobs/
├── __init__.py           # Public exports
├── enums.py              # JobStatus, JobPriority, OutboxEventStatus, OutboxEventType
├── exceptions.py         # JobError hierarchy with RFC 9457 error codes
├── schemas.py            # Pydantic v2 validation contracts
├── lifecycle.py          # State machine transitions and validations
├── retry.py              # Exponential backoff, jitter, and classification
├── registry.py           # Typed task registry (TaskDefinition, TaskRegistry)
├── dispatcher.py         # Transactional outbox event dispatcher
└── service.py            # Workspace-scoped job orchestration service

apps/api/src/dera_api/workers/
├── __init__.py           # Worker exports
├── celery_app.py         # Celery instance configuration (JSON-only, acks_late)
├── tasks.py              # Execution wrappers with CAS claiming and timeouts
└── health.py             # Broker and worker health diagnostic probes
```

## Documentation Index

- [Architecture Overview](ARCHITECTURE.md)
- [Job Lifecycle & State Machine](JOB_LIFECYCLE.md)
- [Task Registry & Whitelist](TASK_REGISTRY.md)
- [Retry, Backoff & Timeout Policy](RETRY_AND_TIMEOUT_POLICY.md)
- [Idempotency & Deduplication](IDEMPOTENCY.md)
- [Cancellation Semantics](CANCELLATION.md)
- [Worker Operations & Concurrency](WORKER_OPERATIONS.md)
- [Failure Recovery & Outbox Delivery](FAILURE_RECOVERY.md)
- [Security & Tenant Isolation](SECURITY_AND_TENANCY.md)
- [Local Development Guide](LOCAL_DEVELOPMENT.md)
- [Testing & Conformance](TESTING.md)
