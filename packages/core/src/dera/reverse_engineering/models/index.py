"""DERA Reverse Engineering — Phase 6.1 Index Model.

Re-exports CanonicalIndex and CanonicalIndexTerm with domain-level type alias IndexRepresentation.
"""

from __future__ import annotations

from dera.metadata.models.index import CanonicalIndex, CanonicalIndexTerm

# Type alias representing index-level canonical schema object
IndexRepresentation = CanonicalIndex

__all__ = ["CanonicalIndex", "CanonicalIndexTerm", "IndexRepresentation"]
