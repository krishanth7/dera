"""Immutable SQL diagnostic contracts; reuse Phase 8 severity and Phase 10.1 models."""

from typing import Literal

from dera.diagnostics.enums import DiagnosticSeverity
from dera.sql_engineering.models import Analysis, Dialect, Model, Span


class Finding(Model):
    finding_id: str
    rule_id: str
    name: str
    category: str
    severity: DiagnosticSeverity
    description: str
    statement_index: int
    evidence: tuple[str, ...]
    location: Span | None = None
    confidence: Literal["STRUCTURAL_FACT", "SCHEMA_FACT", "REVIEW_HEURISTIC"]
    limitations: tuple[str, ...]
    applicable_dialects: tuple[Dialect, ...]


class Recommendation(Model):
    recommendation_id: str
    finding_id: str
    rule_id: str
    title: str
    description: str
    evidence: tuple[str, ...]
    suggested_action: str
    expected_benefit: str
    limitations: tuple[str, ...]
    manual_review_required: bool = True


class RuleEvaluation(Model):
    rule_id: str
    status: Literal["EVALUATED", "NOT_EVALUATED"]
    reason: str | None = None


class ComplexityFactor(Model):
    name: str
    count: int
    weight: int
    contribution: int


class Complexity(Model):
    score: int
    band: Literal["LOW", "MODERATE", "HIGH"]
    factor_breakdown: tuple[ComplexityFactor, ...]
    scoring_version: str = "1.0.0"
    evidence: str = "Structural AST score; not measured execution cost."


class SqlDiagnosticsReport(Model):
    analysis_status: Literal["COMPLETE", "PARTIAL", "INDETERMINATE"]
    dialect: Dialect
    analysis: Analysis
    complexity: Complexity | None
    findings: tuple[Finding, ...]
    recommendations: tuple[Recommendation, ...]
    rule_evaluations: tuple[RuleEvaluation, ...]
    total_findings: int
    rules_version: str = "1.0.0"
    report_version: str = "1.0.0"
    snapshot_fingerprint: str | None
    fingerprint: str
