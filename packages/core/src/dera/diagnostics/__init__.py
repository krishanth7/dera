"""DERA Diagnostics — Deterministic Schema Intelligence and Diagnostic Rules Engine.

Core package for schema diagnostics, versioned rule registry, reproducible static
analysis, evidence validation, conservative severity derivation, advisory recommendations,
suppression governance, finding prioritization, and explainable reporting.
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
from dera.diagnostics.evidence import (
    DiagnosticEvidence,
    EvidenceCompleteness,
    EvidenceProvenance,
    EvidenceType,
    FindingConfidence,
    TypedDiagnosticEvidence,
    build_evidence_traceability_matrix,
    create_evidence_provenance,
    sanitize_value,
    validate_and_enrich_evidence,
)
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
from dera.diagnostics.governance import (
    DiagnosticSuppression,
    FindingLifecycleState,
    GovernanceAuditRecord,
    InvalidLifecycleTransitionError,
    SuppressionScope,
    SuppressionStatus,
    UnauthorizedSuppressionError,
    create_suppression,
    record_governance_action,
    transition_lifecycle_state,
)
from dera.diagnostics.models import (
    DiagnosticCoverage,
    DiagnosticFinding,
    DiagnosticReport,
    DiagnosticSummaryCounts,
    RuleEvaluation,
    RuleMetadata,
)
from dera.diagnostics.prioritization import (
    FindingClassification,
    PriorityRank,
    classify_rule_finding,
    compute_priority_score,
    derive_priority_rank,
    get_finding_sort_key,
    sort_findings_deterministically,
)
from dera.diagnostics.protocols import DiagnosticRule
from dera.diagnostics.recommendations import (
    RECOMMENDATION_CATALOG,
    RECOMMENDATION_CATALOG_VERSION,
    RecommendationEntry,
    RecommendationSafetyViolationError,
    StructuredRecommendation,
    generate_structured_recommendation,
    get_recommendation_for_rule,
    validate_recommendation_safety,
)
from dera.diagnostics.registry import DiagnosticRuleRegistry
from dera.diagnostics.reports import (
    ReportExplainabilitySummary,
    UnifiedDiagnosticFinding,
    UnifiedDiagnosticReport,
    build_report_explainability,
)
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
from dera.diagnostics.rules.maintainability import (
    ALL_MAINTAINABILITY_RULES,
    ALL_PHASE_8_4_RULES,
    ColumnNullabilityRule,
    ComplexDependencyTopologyRule,
    LobConcentrationRule,
    NamespaceImbalanceRule,
    NamingConsistencyRule,
    ReservedWordUsageRule,
    StructuralCouplingRule,
    TableWidthRule,
)
from dera.diagnostics.rules.relationships import (
    ALL_DEPENDENCY_RULES,
    ALL_PHASE_8_3_RULES,
    ALL_RELATIONSHIP_RULES,
    CompositeForeignKeyMappingRule,
    CrossNamespaceDependenciesRule,
    CyclicDependenciesRule,
    DependencyConcentrationRule,
    DependencyDepthRule,
    RelationshipGraphIntegrityRule,
    StructuralImpactRadiusRule,
    UnresolvedRelationshipTargetsRule,
)
from dera.diagnostics.serialization import (
    compute_report_content_hash,
    deserialize_diagnostic_report,
    serialize_diagnostic_report,
)
from dera.diagnostics.severity import (
    SEVERITY_POLICY_VERSION,
    SeverityOverride,
    UnauthorizedSeverityOverrideError,
    build_severity_rationale,
    create_severity_override,
    derive_effective_severity,
    validate_severity_override,
)

ALL_PHASE_8_2_RULES = [
    *ALL_INDEX_RULES,
    *ALL_CONSTRAINT_RULES,
]

ALL_RULES = [
    *ALL_FOUNDATIONAL_RULES,
    *ALL_PHASE_8_2_RULES,
    *ALL_PHASE_8_3_RULES,
    *ALL_PHASE_8_4_RULES,
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
    # Models & Evidence (Phase 8.1 & 8.5)
    "DiagnosticCoverage",
    "DiagnosticEvidence",
    "DiagnosticFinding",
    "DiagnosticReport",
    "DiagnosticSummaryCounts",
    "EvidenceCompleteness",
    "EvidenceProvenance",
    "EvidenceType",
    "FindingConfidence",
    "LegacyDiagnosticFinding",
    "RuleEvaluation",
    "RuleMetadata",
    "TypedDiagnosticEvidence",
    "build_evidence_traceability_matrix",
    "create_evidence_provenance",
    "sanitize_value",
    "validate_and_enrich_evidence",
    # Prioritization & Classification (Phase 8.5)
    "FindingClassification",
    "PriorityRank",
    "classify_rule_finding",
    "compute_priority_score",
    "derive_priority_rank",
    "get_finding_sort_key",
    "sort_findings_deterministically",
    # Severity & Rationale & Overrides (Phase 8.5)
    "SEVERITY_POLICY_VERSION",
    "SeverityOverride",
    "UnauthorizedSeverityOverrideError",
    "build_severity_rationale",
    "create_severity_override",
    "derive_effective_severity",
    "validate_severity_override",
    # Recommendations & Safety (Phase 8.5)
    "RECOMMENDATION_CATALOG",
    "RECOMMENDATION_CATALOG_VERSION",
    "RecommendationEntry",
    "RecommendationSafetyViolationError",
    "StructuredRecommendation",
    "generate_structured_recommendation",
    "get_recommendation_for_rule",
    "validate_recommendation_safety",
    # Governance & Suppressions & Lifecycle (Phase 8.5)
    "DiagnosticSuppression",
    "FindingLifecycleState",
    "GovernanceAuditRecord",
    "InvalidLifecycleTransitionError",
    "SuppressionScope",
    "SuppressionStatus",
    "UnauthorizedSuppressionError",
    "create_suppression",
    "record_governance_action",
    "transition_lifecycle_state",
    # Reports & Explainability (Phase 8.5)
    "ReportExplainabilitySummary",
    "UnifiedDiagnosticFinding",
    "UnifiedDiagnosticReport",
    "build_report_explainability",
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
    # Relationship & Dependency Rules (Phase 8.3)
    "ALL_RELATIONSHIP_RULES",
    "ALL_DEPENDENCY_RULES",
    "ALL_PHASE_8_3_RULES",
    "RelationshipGraphIntegrityRule",
    "UnresolvedRelationshipTargetsRule",
    "CompositeForeignKeyMappingRule",
    "CrossNamespaceDependenciesRule",
    "CyclicDependenciesRule",
    "DependencyDepthRule",
    "DependencyConcentrationRule",
    "StructuralImpactRadiusRule",
    # Maintainability Rules (Phase 8.4)
    "ALL_MAINTAINABILITY_RULES",
    "ALL_PHASE_8_4_RULES",
    "TableWidthRule",
    "ColumnNullabilityRule",
    "NamingConsistencyRule",
    "ReservedWordUsageRule",
    "NamespaceImbalanceRule",
    "StructuralCouplingRule",
    "ComplexDependencyTopologyRule",
    "LobConcentrationRule",
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
