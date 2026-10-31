"""DERA Diagnostics: Index Rules."""

from __future__ import annotations

from dera.diagnostics.protocols import DiagnosticRule
from dera.diagnostics.rules.indexes.duplicate_indexes import DuplicateIndexesRule
from dera.diagnostics.rules.indexes.fk_index_coverage import FkIndexCoverageRule
from dera.diagnostics.rules.indexes.index_column_integrity import IndexColumnIntegrityRule
from dera.diagnostics.rules.indexes.redundant_indexes import RedundantIndexesRule

ALL_INDEX_RULES: list[DiagnosticRule] = [
    DuplicateIndexesRule(),
    RedundantIndexesRule(),
    FkIndexCoverageRule(),
    IndexColumnIntegrityRule(),
]

__all__ = [
    "DuplicateIndexesRule",
    "RedundantIndexesRule",
    "FkIndexCoverageRule",
    "IndexColumnIntegrityRule",
    "ALL_INDEX_RULES",
]
