# Retry, Backoff & Timeout Policy

## Exponential Backoff with Jitter

Transient failures (network dropouts, temporary broker disconnection) trigger deterministic exponential backoff calculated via `calculate_backoff`:

$$\text{delay} = \min(\text{max\_delay}, \text{base\_delay} \times 2^{\text{attempt} - 1})$$

When `jitter=True`, delay is perturbed within $[\text{delay} \times (1 - \text{factor}), \min(\text{max\_delay}, \text{delay} \times (1 + \text{factor}))]$ to prevent thundering herd problems across distributed workers.

## Error Classification

Exceptions during job execution are categorized into:
- **Retryable:** Network timeouts, database lock timeouts, connection resets.
- **Non-Retryable:** Payload schema validation errors, authentication failures, missing permissions, unsupported task types.

Non-retryable errors immediately mark the job as `FAILED` without burning retry attempts.

## Timeout Bounds

Every job type has a bounded execution window (`default_timeout_seconds` or per-job `timeout_seconds`). Workers wrap task execution with `asyncio.wait_for` (or thread timeouts). Exceeding this limit immediately terminates the job and records `JOB_TIMEOUT`. Infinite execution is strictly disallowed.
