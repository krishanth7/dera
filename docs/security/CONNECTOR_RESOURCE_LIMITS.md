# Connector Resource Limits & DoS Defense

**Project:** DERA — Database Engineering & Reverse Analysis  
**Repository:** [https://github.com/krishanth7/dera](https://github.com/krishanth7/dera)  
**Milestone:** Phase 5.6 — Read-Only Enforcement, Timeouts & Safety  
**Auditor:** Principal Application Security Architect & DevSecOps Engineering Team  

---

## 1. Denial-of-Service Defense Overview

Customer databases may contain pathological schema constructs designed either intentionally or inadvertently to cause memory exhaustion, buffer overflows, or unbounded CPU consumption:
- Enormous result row counts (e.g. millions of partitioned tables or columns).
- Excessively long object identifiers (buffer overflow or memory bloat attempts).
- Massive SQL view definitions or check expressions (megabytes of text).
- Excessive concurrency overwhelming DERA worker threads or database connection limits.

DERA enforces deterministic upper bounds via [`ConnectorResourceLimits`](../../packages/connectors/src/dera_connectors/security/resource_limits.py).

---

## 2. Resource Limit Thresholds

| Metric | Upper Safety Limit | Enforcement Method | Exception on Breach |
| :--- | :--- | :--- | :--- |
| **Max Result Rows** | 50,000 rows | `check_result_rows` | `ResourceLimitExceededViolationError` |
| **Max Identifier Length** | 1,024 characters | `check_identifier_length` | `ResourceLimitExceededViolationError` |
| **Max SQL Definition Size** | 1,048,576 bytes (1 MB) | `check_definition_size` | `ResourceLimitExceededViolationError` |
| **Max Schema Objects** | 100,000 entities | `check_metadata_object_count` | `ResourceLimitExceededViolationError` |
| **Max Concurrent Tasks / WS** | 10 active tasks | Semaphores in worker tasks | `ResourceLimitExceededViolationError` |
| **Max Connection Pool Size** | 10 connections | Pool sizing in manager | Bounded queue wait with timeout |
| **Max Retry Attempts** | 3 attempts (transient only) | `is_error_retryable` | Fail closed |

---

## 3. Strict Non-Retryable Error Policy

Retrying security violations, permission errors, or invalid configurations wastes system resources and risks triggering security alerts on customer infrastructure.

The following error classes are **strictly non-retryable**:
- `ConnectorSecurityError` (and all derived security violations)
- `ReadOnlySecurityViolationError`
- `SSRFSecurityViolationError`
- `TenantIsolationViolationError`
- `PermissionError` / `ConnectorPermissionDeniedError`
- `ConnectorAuthenticationError`
- `ConnectorInvalidConfigurationError`

Only transient network socket resets, temporary lock acquisition timeouts, or connection dropped errors are eligible for exponential backoff retries up to `max_retry_attempts`.
