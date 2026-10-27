"""DERA Canonical Metadata Normalization & Identity — Trigger Model.

Defines the strongly-typed CanonicalTrigger model representing procedural triggers.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from dera.metadata.enums import TriggerEvent, TriggerTiming
from dera.metadata.provenance import MetadataProvenance


class CanonicalTrigger(BaseModel):
    """Canonical model for relational database triggers."""

    model_config = ConfigDict(frozen=True)

    id: str = Field(
        ...,
        description="Deterministic canonical ObjectId for this trigger.",
    )
    parent_table_id: str = Field(
        ...,
        description="ObjectId of the target table or view on which trigger fires.",
    )
    name: str = Field(
        ...,
        description="Native trigger identifier.",
    )
    timing: TriggerTiming = Field(
        default=TriggerTiming.BEFORE,
        description="Execution timing: BEFORE, AFTER, or INSTEAD OF.",
    )
    event: TriggerEvent = Field(
        default=TriggerEvent.INSERT,
        description="Triggering DML action: INSERT, UPDATE, DELETE, or TRUNCATE.",
    )
    definition: str | None = Field(
        default=None,
        description="Raw procedural body or statement definition text.",
    )
    provenance: MetadataProvenance = Field(
        ...,
        description="Source extraction provenance and audit information.",
    )
