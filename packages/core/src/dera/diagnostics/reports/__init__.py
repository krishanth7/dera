"""DERA Diagnostics — Reports Subsystem.

Exposes unified diagnostic models and explainability summaries.
"""

from __future__ import annotations

from dera.diagnostics.reports.explainability import (
    ReportExplainabilitySummary,
    build_report_explainability,
)
from dera.diagnostics.reports.unified_models import (
    UnifiedDiagnosticFinding,
    UnifiedDiagnosticReport,
)

__all__ = [
    "ReportExplainabilitySummary",
    "UnifiedDiagnosticFinding",
    "UnifiedDiagnosticReport",
    "build_report_explainability",
]
