"""DERA Auth — In-Memory Abuse Protection and Rate Limiting.

Provides bounded rate-limiting for authentication endpoints (e.g., login attempts)
to protect against credential stuffing and brute-force attacks.
"""

import threading
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass
class AttemptRecord:
    """Tracking structure for failed authentication attempts."""

    timestamps: list[datetime] = field(default_factory=list)


class AuthRateLimiter:
    """Thread-safe bounded in-memory rate limiter for authentication endpoints."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._records: dict[str, AttemptRecord] = defaultdict(AttemptRecord)

    def is_rate_limited(
        self,
        key: str,
        max_attempts: int = 5,
        window_seconds: int = 300,
    ) -> bool:
        """Check if the given key has exceeded allowed failed attempts within the sliding window."""
        now = datetime.now(UTC)
        threshold = now.timestamp() - window_seconds

        with self._lock:
            record = self._records.get(key)
            if not record:
                return False

            # Prune expired timestamps
            record.timestamps = [t for t in record.timestamps if t.timestamp() > threshold]
            if not record.timestamps:
                self._records.pop(key, None)
                return False

            return len(record.timestamps) >= max_attempts

    def record_failure(
        self,
        key: str,
        window_seconds: int = 300,
    ) -> int:
        """Record a failed attempt for the given key and return current attempt count."""
        now = datetime.now(UTC)
        threshold = now.timestamp() - window_seconds

        with self._lock:
            record = self._records[key]
            record.timestamps = [t for t in record.timestamps if t.timestamp() > threshold]
            record.timestamps.append(now)
            return len(record.timestamps)

    def reset(self, key: str) -> None:
        """Clear recorded failed attempts for the given key upon successful authentication."""
        with self._lock:
            self._records.pop(key, None)

    def clear(self) -> None:
        """Clear all rate limit records (primarily for testing isolation)."""
        with self._lock:
            self._records.clear()


# Global default rate limiter instance
auth_rate_limiter = AuthRateLimiter()
