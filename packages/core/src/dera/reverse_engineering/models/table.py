"""DERA Reverse Engineering — Phase 6.1 Table Model.

Re-exports CanonicalTable with domain-level type alias TableRepresentation.
"""

from __future__ import annotations

from dera.metadata.models.table import CanonicalTable

# Type alias representing table-level canonical schema object
TableRepresentation = CanonicalTable

__all__ = ["CanonicalTable", "TableRepresentation"]
