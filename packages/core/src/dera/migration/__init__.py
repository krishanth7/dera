"""DERA Migration — Phase 9.2 Package Initialization.

Exports the MigrationRiskAnalysisEngine, models, enums, and exceptions.
"""

from __future__ import annotations

from dera.migration.classification.models import ClassifiedChange
from dera.migration.engine import MigrationRiskAnalysisEngine
from dera.migration.enums import (
    CompatibilityLevel,
    ReversibilityClassification,
    ReviewPriority,
    RiskDimension,
    RiskEvidenceCertainty,
    StructuralChangeCategory,
    TypeConversionSafety,
)
from dera.migration.errors import (
    IncompleteGraphMetadataError,
    InvalidComparisonReportError,
    MigrationRiskAnalysisError,
    RiskResourceLimitExceededError,
)
from dera.migration.impact.blast_radius import (
    BlastRadiusMetrics,
    DependencyImpactAnalyzer,
    DependentObject,
)
from dera.migration.limits import MigrationRiskLimits
from dera.migration.recommendations.models import EngineeringRecommendation
from dera.migration.reports.models import (
    MIGRATION_POLICY_VERSION,
    MigrationRiskReport,
    MigrationRiskSummary,
)
from dera.migration.risk.models import MigrationRiskAssessment

__all__ = [
    "BlastRadiusMetrics",
    "ClassifiedChange",
    "CompatibilityLevel",
    "DependencyImpactAnalyzer",
    "DependentObject",
    "EngineeringRecommendation",
    "IncompleteGraphMetadataError",
    "InvalidComparisonReportError",
    "MIGRATION_POLICY_VERSION",
    "MigrationRiskAnalysisEngine",
    "MigrationRiskAnalysisError",
    "MigrationRiskAssessment",
    "MigrationRiskLimits",
    "MigrationRiskReport",
    "MigrationRiskSummary",
    "ReversibilityClassification",
    "ReviewPriority",
    "RiskDimension",
    "RiskEvidenceCertainty",
    "RiskResourceLimitExceededError",
    "StructuralChangeCategory",
    "TypeConversionSafety",
]
