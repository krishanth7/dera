"""DERA Reverse Engineering — Phase 6.1 View Model.

Re-exports CanonicalView with domain-level type alias ViewRepresentation.
"""

from __future__ import annotations

from dera.metadata.models.view import CanonicalView

# Type alias representing view-level canonical schema object
ViewRepresentation = CanonicalView

__all__ = ["CanonicalView", "ViewRepresentation"]
