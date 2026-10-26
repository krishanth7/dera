"""Deterministic diagnostic rule engine for DERA.

Evaluates schema models against reproducible, static engineering rules
to detect structural defects without non-deterministic AI models.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable
from dera.models import DatabaseTable


class RuleSeverity(str, Enum):
    """Severity classification for diagnostic findings."""

    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


@dataclass(frozen=True)
class DiagnosticFinding:
    """Represents an evidence-based diagnostic finding."""

    rule_id: str
    category: str
    severity: RuleSeverity
    table: str
    message: str
    remediation_ddl: str | None = None


def evaluate_missing_primary_keys(tables: Iterable[DatabaseTable]) -> list[DiagnosticFinding]:
    """Detects tables lacking explicit primary key constraints."""
    findings: list[DiagnosticFinding] = []
    for table in tables:
        if table.primary_key is None or len(table.primary_key.columns) == 0:
            findings.append(
                DiagnosticFinding(
                    rule_id="RULE-INT-001",
                    category="Integrity",
                    severity=RuleSeverity.ERROR,
                    table=table.fully_qualified_name,
                    message=f"Table '{table.fully_qualified_name}' lacks a primary key constraint.",
                    remediation_ddl=f"ALTER TABLE {table.fully_qualified_name} ADD PRIMARY KEY (<id_column>);",
                )
            )
    return findings


def evaluate_unindexed_foreign_keys(tables: Iterable[DatabaseTable]) -> list[DiagnosticFinding]:
    """Detects foreign-key columns lacking supporting index coverage."""
    findings: list[DiagnosticFinding] = []
    for table in tables:
        indexed_prefixes = {idx.columns[0] for idx in table.indexes if idx.columns}
        for fk in table.foreign_keys:
            if fk.source_columns and fk.source_columns[0] not in indexed_prefixes:
                cols_str = ", ".join(fk.source_columns)
                idx_name = f"idx_{table.name}_{fk.source_columns[0]}"
                findings.append(
                    DiagnosticFinding(
                        rule_id="RULE-PERF-002",
                        category="Performance",
                        severity=RuleSeverity.WARNING,
                        table=table.fully_qualified_name,
                        message=(
                            f"Foreign key '{fk.name}' on columns ({cols_str}) "
                            f"lacks an index starting with '{fk.source_columns[0]}'."
                        ),
                        remediation_ddl=f"CREATE INDEX {idx_name} ON {table.fully_qualified_name} ({cols_str});",
                    )
                )
    return findings


def run_all_diagnostics(tables: Iterable[DatabaseTable]) -> list[DiagnosticFinding]:
    """Executes the complete deterministic diagnostic rule matrix."""
    table_list = list(tables)
    findings: list[DiagnosticFinding] = []
    findings.extend(evaluate_missing_primary_keys(table_list))
    findings.extend(evaluate_unindexed_foreign_keys(table_list))
    return sorted(findings, key=lambda x: (x.severity.value, x.table, x.rule_id))
