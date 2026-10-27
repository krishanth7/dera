"""DERA Core — Database Engineering & Reverse Analysis Core Package.

This package provides deterministic schema models, graph DAG topological sorting,
Tarjan's cycle detection, and rule-based diagnostics without AI runtime dependencies.
"""

from dera.diagnostics import (
    RuleSeverity,
    run_all_diagnostics,
)
from dera.graph import (
    build_dependency_graph,
    compute_topological_sort,
)
from dera.models import (
    Column,
    DatabaseColumn,
    DatabaseTable,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    PrimaryKeyConstraint,
    SchemaSnapshot,
    Table,
    TableIndex,
)

from dera_core.exceptions import (
    ConfigurationError,
    ConnectionAuthenticationError,
    ConnectorError,
    CycleDetectedError,
    DeraError,
    DiagnosticRuleError,
    ReadOnlyViolationError,
    SchemaParsingError,
)

__version__ = "0.1.0-dev"

__all__ = [
    "Column",
    "ConfigurationError",
    "ConnectionAuthenticationError",
    "ConnectorError",
    "CycleDetectedError",
    "DatabaseColumn",
    "DatabaseTable",
    "DeraError",
    "DiagnosticRuleError",
    "ForeignKey",
    "ForeignKeyConstraint",
    "Index",
    "PrimaryKeyConstraint",
    "ReadOnlyViolationError",
    "RuleSeverity",
    "SchemaParsingError",
    "SchemaSnapshot",
    "Table",
    "TableIndex",
    "__version__",
    "build_dependency_graph",
    "compute_topological_sort",
    "run_all_diagnostics",
]
