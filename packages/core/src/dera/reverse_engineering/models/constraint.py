"""DERA Reverse Engineering — Phase 6.1 Constraint Model.

Re-exports CanonicalConstraint with domain-level type alias ConstraintRepresentation.
"""

from __future__ import annotations

from dera.metadata.models.constraint import CanonicalConstraint

# Type alias representing constraint-level canonical schema object
ConstraintRepresentation = CanonicalConstraint

__all__ = ["CanonicalConstraint", "ConstraintRepresentation"]
