"""DERA Diagnostics — Deterministic Schema Intelligence and Diagnostic Rules Engine.

Core package for Phase 8.1 schema diagnostics, versioned rule registry,
reproducible static linting, and evidence-based finding aggregation.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import TYPE_CHECKING

from dera.diagnostics.applicability import check_rule_applicability
from dera.diagnostics.context import (
    DiagnosticContext,
    DiagnosticEngineConfig,
    DiagnosticResourceLimits,
)
from dera.diagnostics.enums import (
    ApplicabilityStatus,
    DiagnosticSeverity,
    EvaluationStatus,
    RuleCategory,
    RuleSeverity,
)
from dera.diagnostics.evaluator import DiagnosticEvaluator
from dera.diagnostics.evidence import DiagnosticEvidence, sanitize_value
from dera.diagnostics.exceptions import (
    DiagnosticEngineError,
    DuplicateRuleError,
    InvalidContextError,
    InvalidRuleMetadataError,
    ResourceLimitExceededError,
    RuleEvaluationError,
    RuleNotFoundError,
)
from dera.diagnostics.fingerprint import (
    compute_config_fingerprint,
    compute_finding_fingerprint,
)
from dera.diagnostics.models import (
    DiagnosticCoverage,
    DiagnosticFinding,
    DiagnosticReport,
    DiagnosticSummaryCounts,
    RuleEvaluation,
    RuleMetadata,
)
from dera.diagnostics.protocols import DiagnosticRule
from dera.diagnostics.registry import DiagnosticRuleRegistry
from dera.diagnostics.rules.constraints import (
    ALL_CONSTRAINT_RULES,
    CheckConstraintMetadataRule,
    ConstraintColumnIntegrityRule,
    ForeignKeyIntegrityRule,
    PrimaryKeyIntegrityRule,
    UniqueConstraintIntegrityRule,
)
from dera.diagnostics.rules.foundational import (
    ALL_FOUNDATIONAL_RULES,
    CanonicalIdentityCollisionRule,
    InvalidRelationshipMappingRule,
    MissingStructuralMetadataRule,
    UnresolvedRelationshipTargetRule,
    UnsupportedCapabilityRule,
)
from dera.diagnostics.rules.indexes import (
    ALL_INDEX_RULES,
    DuplicateIndexesRule,
    FkIndexCoverageRule,
    IndexColumnIntegrityRule,
    RedundantIndexesRule,
)
from dera.diagnostics.serialization import (
    compute_report_content_hash,
    deserialize_diagnostic_report,
    serialize_diagnostic_report,
)

ALL_PHASE_8_2_RULES = [
    *ALL_INDEX_RULES,
    *ALL_CONSTRAINT_RULES,
]

ALL_RULES = [
    *ALL_FOUNDATIONAL_RULES,
    *ALL_PHASE_8_2_RULES,
]

if TYPE_CHECKING:
    from dera.models import DatabaseTable


# ---------------------------------------------------------------------------
# Legacy Backwards-Compatibility Layer (Phase 1-6 support)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class LegacyDiagnosticFinding:
    """Legacy finding format matching Phase 1-6 tests and connectors."""

    rule_id: str
    category: str
    severity: RuleSeverity
    table: str
    message: str
    remediation_ddl: str | None = None


def evaluate_missing_primary_keys(tables: Iterable[DatabaseTable]) -> list[LegacyDiagnosticFinding]:
    """Legacy check: detects tables lacking explicit primary key constraints."""
    findings: list[LegacyDiagnosticFinding] = []
    for table in tables:
        if table.primary_key is None or len(table.primary_key.columns) == 0:
            findings.append(
                LegacyDiagnosticFinding(
                    rule_id="RULE-INT-001",
                    category="Integrity",
                    severity=RuleSeverity.ERROR,
                    table=table.fully_qualified_name,
                    message=f"Table '{table.fully_qualified_name}' lacks a primary key constraint.",
                    remediation_ddl=f"ALTER TABLE {table.fully_qualified_name} ADD PRIMARY KEY (<id_column>);",
                )
            )
    return findings


def evaluate_unindexed_foreign_keys(
    tables: Iterable[DatabaseTable],
) -> list[LegacyDiagnosticFinding]:
    """Legacy check: detects foreign-key columns lacking supporting index coverage."""
    findings: list[LegacyDiagnosticFinding] = []
    for table in tables:
        indexed_prefixes = {idx.columns[0] for idx in table.indexes if idx.columns}
        for fk in table.foreign_keys:
            if fk.source_columns and fk.source_columns[0] not in indexed_prefixes:
                cols_str = ", ".join(fk.source_columns)
                idx_name = f"idx_{table.name}_{fk.source_columns[0]}"
                findings.append(
                    LegacyDiagnosticFinding(
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


def run_all_diagnostics(tables: Iterable[DatabaseTable]) -> list[LegacyDiagnosticFinding]:
    """Legacy execution entrypoint executing legacy diagnostic checks."""
    table_list = list(tables)
    findings: list[LegacyDiagnosticFinding] = []
    findings.extend(evaluate_missing_primary_keys(table_list))
    findings.extend(evaluate_unindexed_foreign_keys(table_list))
    return sorted(findings, key=lambda x: (x.severity.value, x.table, x.rule_id))


__all__ = [
    # Enums
    "ApplicabilityStatus",
    "DiagnosticSeverity",
    "EvaluationStatus",
    "RuleCategory",
    "RuleSeverity",
    # Models & Evidence
    "DiagnosticCoverage",
    "DiagnosticEvidence",
    "DiagnosticFinding",
    "DiagnosticReport",
    "DiagnosticSummaryCounts",
    "LegacyDiagnosticFinding",
    "RuleEvaluation",
    "RuleMetadata",
    "sanitize_value",
    # Context & Protocols
    "DiagnosticContext",
    "DiagnosticEngineConfig",
    "DiagnosticResourceLimits",
    "DiagnosticRule",
    # Registry & Evaluator
    "DiagnosticEvaluator",
    "DiagnosticRuleRegistry",
    "check_rule_applicability",
    # Fingerprint & Serialization
    "compute_config_fingerprint",
    "compute_finding_fingerprint",
    "compute_report_content_hash",
    "deserialize_diagnostic_report",
    "serialize_diagnostic_report",
    # Foundational Rules
    "ALL_FOUNDATIONAL_RULES",
    "CanonicalIdentityCollisionRule",
    "InvalidRelationshipMappingRule",
    "MissingStructuralMetadataRule",
    "UnresolvedRelationshipTargetRule",
    "UnsupportedCapabilityRule",
    # Index Rules
    "ALL_INDEX_RULES",
    "DuplicateIndexesRule",
    "RedundantIndexesRule",
    "FkIndexCoverageRule",
    "IndexColumnIntegrityRule",
    # Constraint Rules
    "ALL_CONSTRAINT_RULES",
    "PrimaryKeyIntegrityRule",
    "ForeignKeyIntegrityRule",
    "UniqueConstraintIntegrityRule",
    "CheckConstraintMetadataRule",
    "ConstraintColumnIntegrityRule",
    # Aggregations
    "ALL_PHASE_8_2_RULES",
    "ALL_RULES",
    # Exceptions
    "DiagnosticEngineError",
    "DuplicateRuleError",
    "InvalidContextError",
    "InvalidRuleMetadataError",
    "ResourceLimitExceededError",
    "RuleEvaluationError",
    "RuleNotFoundError",
    # Legacy Shims
    "evaluate_missing_primary_keys",
    "evaluate_unindexed_foreign_keys",
    "run_all_diagnostics",
]
