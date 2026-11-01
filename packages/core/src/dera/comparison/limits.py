"""DERA Comparison — Phase 9.1 Resource Limits.

Enforces execution bounds on table count, column count, total diff entries,
and serialization payload sizes to prevent unbounded compute or denial-of-service.
"""

from __future__ import annotations

from dataclasses import dataclass

from dera.comparison.errors import ComparisonResourceLimitExceededError


@dataclass(frozen=True)
class ComparisonResourceLimits:
    """Configurable resource safety boundaries for snapshot comparison."""

    max_tables: int = 5_000
    max_columns: int = 50_000
    max_indexes: int = 25_000
    max_constraints: int = 25_000
    max_differences: int = 100_000
    max_report_bytes: int = 50_000_000  # 50 MB JSON limit

    def check_table_count(self, count: int, label: str = "snapshot") -> None:
        """Validate table count against limit."""
        if count > self.max_tables:
            raise ComparisonResourceLimitExceededError(
                message=f"Table count {count} in {label} exceeds safety limit of {self.max_tables}.",
                limit_name="max_tables",
                actual_value=count,
                max_value=self.max_tables,
            )

    def check_column_count(self, count: int, label: str = "snapshot") -> None:
        """Validate column count against limit."""
        if count > self.max_columns:
            raise ComparisonResourceLimitExceededError(
                message=f"Total column count {count} in {label} exceeds safety limit of {self.max_columns}.",
                limit_name="max_columns",
                actual_value=count,
                max_value=self.max_columns,
            )

    def check_difference_count(self, count: int) -> None:
        """Validate generated difference entries against limit."""
        if count > self.max_differences:
            raise ComparisonResourceLimitExceededError(
                message=f"Total differences count {count} exceeds safety limit of {self.max_differences}.",
                limit_name="max_differences",
                actual_value=count,
                max_value=self.max_differences,
            )
