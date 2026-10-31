"""DERA Diagnostics — Maintainability Diagnostic Rules Catalog.

Exposes Phase 8.4 schema maintainability rules auditing table width,
column nullability, naming consistency, reserved word clashes, namespace imbalance,
structural coupling, complex dependencies, and LOB column concentration.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from dera.diagnostics.rules.maintainability.column_nullability import ColumnNullabilityRule
from dera.diagnostics.rules.maintainability.complex_dependencies import (
    ComplexDependencyTopologyRule,
)
from dera.diagnostics.rules.maintainability.lob_concentration import LobConcentrationRule
from dera.diagnostics.rules.maintainability.namespace_imbalance import NamespaceImbalanceRule
from dera.diagnostics.rules.maintainability.naming_consistency import NamingConsistencyRule
from dera.diagnostics.rules.maintainability.reserved_words import ReservedWordUsageRule
from dera.diagnostics.rules.maintainability.structural_coupling import StructuralCouplingRule
from dera.diagnostics.rules.maintainability.table_width import TableWidthRule

if TYPE_CHECKING:
    from dera.diagnostics.protocols import DiagnosticRule

ALL_MAINTAINABILITY_RULES: tuple[DiagnosticRule, ...] = (
    TableWidthRule(),
    ColumnNullabilityRule(),
    NamingConsistencyRule(),
    ReservedWordUsageRule(),
    NamespaceImbalanceRule(),
    StructuralCouplingRule(),
    ComplexDependencyTopologyRule(),
    LobConcentrationRule(),
)

ALL_PHASE_8_4_RULES: tuple[DiagnosticRule, ...] = ALL_MAINTAINABILITY_RULES

__all__ = [
    "ALL_MAINTAINABILITY_RULES",
    "ALL_PHASE_8_4_RULES",
    "ColumnNullabilityRule",
    "ComplexDependencyTopologyRule",
    "LobConcentrationRule",
    "NamespaceImbalanceRule",
    "NamingConsistencyRule",
    "ReservedWordUsageRule",
    "StructuralCouplingRule",
    "TableWidthRule",
]
