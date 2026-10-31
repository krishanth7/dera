"""DERA Diagnostics — Foundational Rules Catalog.

Exposes the core foundational diagnostic rules validated in Phase 8.1.
"""

from __future__ import annotations

from dera.diagnostics.rules.foundational.identity_collision import CanonicalIdentityCollisionRule
from dera.diagnostics.rules.foundational.invalid_mapping import InvalidRelationshipMappingRule
from dera.diagnostics.rules.foundational.missing_structural_metadata import (
    MissingStructuralMetadataRule,
)
from dera.diagnostics.rules.foundational.unresolved_target import (
    UnresolvedRelationshipTargetRule,
)
from dera.diagnostics.rules.foundational.unsupported_capability import (
    UnsupportedCapabilityRule,
)

ALL_FOUNDATIONAL_RULES = (
    UnresolvedRelationshipTargetRule(),
    CanonicalIdentityCollisionRule(),
    InvalidRelationshipMappingRule(),
    MissingStructuralMetadataRule(),
    UnsupportedCapabilityRule(),
)

__all__ = [
    "ALL_FOUNDATIONAL_RULES",
    "CanonicalIdentityCollisionRule",
    "InvalidRelationshipMappingRule",
    "MissingStructuralMetadataRule",
    "UnresolvedRelationshipTargetRule",
    "UnsupportedCapabilityRule",
]
