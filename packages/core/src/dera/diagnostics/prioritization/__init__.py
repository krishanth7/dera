"""DERA Diagnostics — Prioritization Subsystem.

Exposes finding classification, multi-factor ranking, and deterministic ordering.
"""

from __future__ import annotations

from dera.diagnostics.prioritization.classification import (
    FindingClassification,
    classify_rule_finding,
)
from dera.diagnostics.prioritization.ordering import (
    get_finding_sort_key,
    sort_findings_deterministically,
)
from dera.diagnostics.prioritization.ranking import (
    PriorityRank,
    compute_priority_score,
    derive_priority_rank,
)

__all__ = [
    "FindingClassification",
    "PriorityRank",
    "classify_rule_finding",
    "compute_priority_score",
    "derive_priority_rank",
    "get_finding_sort_key",
    "sort_findings_deterministically",
]
