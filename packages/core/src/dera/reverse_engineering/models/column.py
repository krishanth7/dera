"""DERA Reverse Engineering — Phase 6.1 Column Model.

Re-exports CanonicalColumn with domain-level type alias ColumnRepresentation.
"""

from __future__ import annotations

from dera.metadata.models.column import CanonicalColumn

# Type alias representing column-level canonical schema object
ColumnRepresentation = CanonicalColumn

__all__ = ["CanonicalColumn", "ColumnRepresentation"]
