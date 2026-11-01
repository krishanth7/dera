"""DERA Diagnostics — Maintainability Metrics Engine.

Provides deterministic metric models and calculators for evaluating
schema complexity, table composition, naming conventions, namespace distributions,
and structural coupling.
"""

from __future__ import annotations

from dera.diagnostics.metrics.coupling_metrics import compute_all_coupling_metrics
from dera.diagnostics.metrics.models import (
    CouplingMaintainabilityMetrics,
    MaintainabilityMetricDefinition,
    MaintainabilityMetricScope,
    MaintainabilityMetricsReport,
    NamespaceMaintainabilityMetrics,
    NamingComplianceMetrics,
    SchemaComplexityMetrics,
    TableMaintainabilityMetrics,
)
from dera.diagnostics.metrics.namespace_metrics import (
    compute_namespace_imbalance_ratio,
    compute_namespace_metrics,
)
from dera.diagnostics.metrics.naming_metrics import (
    NamingProfile,
    compute_naming_compliance,
    is_reserved_word,
    matches_naming_profile,
)
from dera.diagnostics.metrics.schema_metrics import compute_schema_complexity
from dera.diagnostics.metrics.table_metrics import (
    compute_all_table_metrics,
    compute_table_metrics,
    is_lob_column,
)

__all__ = [
    "CouplingMaintainabilityMetrics",
    "MaintainabilityMetricDefinition",
    "MaintainabilityMetricScope",
    "MaintainabilityMetricsReport",
    "NamespaceMaintainabilityMetrics",
    "NamingComplianceMetrics",
    "NamingProfile",
    "SchemaComplexityMetrics",
    "TableMaintainabilityMetrics",
    "compute_all_coupling_metrics",
    "compute_all_table_metrics",
    "compute_namespace_imbalance_ratio",
    "compute_namespace_metrics",
    "compute_naming_compliance",
    "compute_schema_complexity",
    "compute_table_metrics",
    "is_lob_column",
    "is_reserved_word",
    "matches_naming_profile",
]
