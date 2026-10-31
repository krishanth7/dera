"""DERA Diagnostics — Finding Classification Taxonomy.

Defines the explicit taxonomy distinguishing confirmed structural defects,
potential engineering concerns, optimization candidates, maintainability concerns,
naming deviations, informational observations, and metadata limitations.
"""

from __future__ import annotations

from enum import StrEnum


class FindingClassification(StrEnum):
    """Categorical classification of a diagnostic finding.

    Distinguishes verifiable defects from stylistic guidelines, optimizations,
    and metadata restrictions. Classification is orthogonal to severity.
    """

    CONFIRMED_STRUCTURAL_DEFECT = "confirmed_structural_defect"
    POTENTIAL_ENGINEERING_CONCERN = "potential_engineering_concern"
    OPTIMIZATION_CANDIDATE = "optimization_candidate"
    MAINTAINABILITY_CONCERN = "maintainability_concern"
    NAMING_CONVENTION_DEVIATION = "naming_convention_deviation"
    INFORMATIONAL_OBSERVATION = "informational_observation"
    METADATA_LIMITATION = "metadata_limitation"
    INTERNAL_INSPECTION_INTEGRITY_ISSUE = "internal_inspection_integrity_issue"

    @property
    def display_name(self) -> str:
        """Human-readable display title for user interfaces and reports."""
        labels = {
            FindingClassification.CONFIRMED_STRUCTURAL_DEFECT: "Confirmed Structural Defect",
            FindingClassification.POTENTIAL_ENGINEERING_CONCERN: "Potential Engineering Concern",
            FindingClassification.OPTIMIZATION_CANDIDATE: "Optimization Candidate",
            FindingClassification.MAINTAINABILITY_CONCERN: "Maintainability Concern",
            FindingClassification.NAMING_CONVENTION_DEVIATION: "Naming Convention Deviation",
            FindingClassification.INFORMATIONAL_OBSERVATION: "Informational Observation",
            FindingClassification.METADATA_LIMITATION: "Metadata Limitation",
            FindingClassification.INTERNAL_INSPECTION_INTEGRITY_ISSUE: "Internal Inspection Integrity Issue",
        }
        return labels[self]

    @property
    def priority_weight(self) -> int:
        """Deterministic priority weight for multi-factor ranking (higher is more critical)."""
        weights = {
            FindingClassification.CONFIRMED_STRUCTURAL_DEFECT: 100,
            FindingClassification.POTENTIAL_ENGINEERING_CONCERN: 80,
            FindingClassification.INTERNAL_INSPECTION_INTEGRITY_ISSUE: 75,
            FindingClassification.OPTIMIZATION_CANDIDATE: 60,
            FindingClassification.MAINTAINABILITY_CONCERN: 50,
            FindingClassification.METADATA_LIMITATION: 40,
            FindingClassification.NAMING_CONVENTION_DEVIATION: 30,
            FindingClassification.INFORMATIONAL_OBSERVATION: 10,
        }
        return weights[self]


def classify_rule_finding(rule_id: str) -> FindingClassification:
    """Deterministically maps a diagnostic rule ID to its canonical finding classification."""
    prefix = rule_id.upper()

    # Integrity & structural defect rules
    if any(
        k in prefix
        for k in (
            "DERA-CON-001",  # Missing PK
            "DERA-CON-002",  # Invalid FK target
            "DERA-CON-003",  # Non-unique column referenced by FK
            "DERA-CON-004",  # Missing check constraint expression
            "DERA-CON-005",  # Constraint references non-existent column
            "DERA-REL-001",  # Relationship graph integrity
            "DERA-REL-002",  # Unresolved relationship target
            "DERA-REL-003",  # Composite FK mapping mismatch
            "DERA-IDX-004",  # Index column integrity (non-existent col)
            "DERA-SCHEMA-001",  # Identity collision
            "DERA-SCHEMA-002",  # Missing structural metadata
            "DERA-SCHEMA-004",  # Invalid relationship mapping
        )
    ):
        return FindingClassification.CONFIRMED_STRUCTURAL_DEFECT

    # Performance / optimization candidates
    if any(
        k in prefix
        for k in (
            "DERA-IDX-001",  # Duplicate indexes
            "DERA-IDX-002",  # Redundant prefix indexes
            "DERA-IDX-003",  # Unindexed foreign keys
            "DERA-DEP-004",  # Structural impact radius
        )
    ):
        return FindingClassification.OPTIMIZATION_CANDIDATE

    # Architecture / engineering concerns
    if any(
        k in prefix
        for k in (
            "DERA-DEP-001",  # Cyclic dependencies
            "DERA-DEP-002",  # Dependency depth
            "DERA-DEP-003",  # Dependency concentration
            "DERA-REL-004",  # Cross-namespace dependencies
            "DERA-MNT-006",  # Structural coupling
            "DERA-MNT-007",  # Complex dependency topology
        )
    ):
        return FindingClassification.POTENTIAL_ENGINEERING_CONCERN

    # Style / naming deviations
    if any(
        k in prefix for k in ("DERA-MNT-003", "DERA-MNT-004")
    ):  # Naming consistency, reserved words
        return FindingClassification.NAMING_CONVENTION_DEVIATION

    # Maintainability concerns
    if any(
        k in prefix
        for k in (
            "DERA-MNT-001",  # Table width
            "DERA-MNT-002",  # Column nullability ratio
            "DERA-MNT-005",  # Namespace imbalance
            "DERA-MNT-008",  # LOB concentration
        )
    ):
        return FindingClassification.MAINTAINABILITY_CONCERN

    # Metadata limitations
    if any(k in prefix for k in ("DERA-SCHEMA-003", "DERA-CAP-", "METADATA")):
        return FindingClassification.METADATA_LIMITATION

    return FindingClassification.POTENTIAL_ENGINEERING_CONCERN
