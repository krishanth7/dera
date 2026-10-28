"""DERA Reverse Engineering — Phase 6.1 Trigger Model.

Re-exports CanonicalTrigger with domain-level type alias TriggerRepresentation.
"""

from __future__ import annotations

from dera.metadata.models.trigger import CanonicalTrigger

# Type alias representing trigger-level canonical schema object
TriggerRepresentation = CanonicalTrigger

__all__ = ["CanonicalTrigger", "TriggerRepresentation"]
