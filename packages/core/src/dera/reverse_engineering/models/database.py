"""DERA Reverse Engineering — Phase 6.1 Database Model.

Re-exports CanonicalDatabase with domain-level type alias DatabaseRepresentation.
Preserves Phase 5.5 identity and serialization contracts without duplication.
"""

from __future__ import annotations

from dera.metadata.models.database import CanonicalDatabase

# Type alias representing database-level canonical schema object
DatabaseRepresentation = CanonicalDatabase

__all__ = ["CanonicalDatabase", "DatabaseRepresentation"]
