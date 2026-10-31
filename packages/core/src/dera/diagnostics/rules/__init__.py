"""DERA Diagnostics — Rule Implementations Catalog.

Contains foundational, index, and constraint diagnostic rules.
"""

from __future__ import annotations

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

ALL_PHASE_8_2_RULES = [
    *ALL_INDEX_RULES,
    *ALL_CONSTRAINT_RULES,
]

ALL_RULES = [
    *ALL_FOUNDATIONAL_RULES,
    *ALL_PHASE_8_2_RULES,
]

__all__ = [
    # Foundational rules
    "ALL_FOUNDATIONAL_RULES",
    "CanonicalIdentityCollisionRule",
    "InvalidRelationshipMappingRule",
    "MissingStructuralMetadataRule",
    "UnresolvedRelationshipTargetRule",
    "UnsupportedCapabilityRule",
    # Index rules
    "ALL_INDEX_RULES",
    "DuplicateIndexesRule",
    "RedundantIndexesRule",
    "FkIndexCoverageRule",
    "IndexColumnIntegrityRule",
    # Constraint rules
    "ALL_CONSTRAINT_RULES",
    "PrimaryKeyIntegrityRule",
    "ForeignKeyIntegrityRule",
    "UniqueConstraintIntegrityRule",
    "CheckConstraintMetadataRule",
    "ConstraintColumnIntegrityRule",
    # Aggregated collections
    "ALL_PHASE_8_2_RULES",
    "ALL_RULES",
]
