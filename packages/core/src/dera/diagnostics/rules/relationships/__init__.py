"""DERA Diagnostics — Phase 8.3 Relationship and Dependency Rules Catalog.

Exposes deterministic static analysis rules for foreign key graph integrity,
composite mapping verification, cyclic dependencies, depth, concentration, and structural impact.
"""

from __future__ import annotations

from dera.diagnostics.protocols import DiagnosticRule
from dera.diagnostics.rules.relationships.composite_mappings import (
    CompositeForeignKeyMappingRule,
)
from dera.diagnostics.rules.relationships.cross_namespace import (
    CrossNamespaceDependenciesRule,
)
from dera.diagnostics.rules.relationships.cyclic_dependencies import (
    CyclicDependenciesRule,
)
from dera.diagnostics.rules.relationships.dependency_concentration import (
    DependencyConcentrationRule,
)
from dera.diagnostics.rules.relationships.dependency_depth import (
    DependencyDepthRule,
)
from dera.diagnostics.rules.relationships.graph_integrity import (
    RelationshipGraphIntegrityRule,
)
from dera.diagnostics.rules.relationships.structural_impact import (
    StructuralImpactRadiusRule,
)
from dera.diagnostics.rules.relationships.unresolved_targets import (
    UnresolvedRelationshipTargetsRule,
)

ALL_RELATIONSHIP_RULES: tuple[DiagnosticRule, ...] = (
    RelationshipGraphIntegrityRule(),
    UnresolvedRelationshipTargetsRule(),
    CompositeForeignKeyMappingRule(),
    CrossNamespaceDependenciesRule(),
)

ALL_DEPENDENCY_RULES: tuple[DiagnosticRule, ...] = (
    CyclicDependenciesRule(),
    DependencyDepthRule(),
    DependencyConcentrationRule(),
    StructuralImpactRadiusRule(),
)

ALL_PHASE_8_3_RULES: tuple[DiagnosticRule, ...] = ALL_RELATIONSHIP_RULES + ALL_DEPENDENCY_RULES

__all__ = [
    "ALL_DEPENDENCY_RULES",
    "ALL_PHASE_8_3_RULES",
    "ALL_RELATIONSHIP_RULES",
    "CompositeForeignKeyMappingRule",
    "CrossNamespaceDependenciesRule",
    "CyclicDependenciesRule",
    "DependencyConcentrationRule",
    "DependencyDepthRule",
    "RelationshipGraphIntegrityRule",
    "StructuralImpactRadiusRule",
    "UnresolvedRelationshipTargetsRule",
]
