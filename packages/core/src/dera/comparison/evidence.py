"""DERA Comparison — Phase 9.1 Evidence Models.

Defines verifiable before-and-after evidence records ensuring no structural
difference is claimed without cryptographic or literal provenance.
"""

from __future__ import annotations

from typing import Any
from pydantic import BaseModel, ConfigDict, Field

from dera.comparison.enums import PropertyComparisonStatus
from dera.metadata.enums import MetadataCompleteness


class ObjectEvidence(BaseModel):
    """Verifiable structural snapshot evidence of a schema object."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    snapshot_id: str = Field(description="Snapshot identifier providing the evidence.")
    object_id: str = Field(description="Canonical ObjectId of the object.")
    namespace: str = Field(description="Schema or namespace of the object.")
    name: str = Field(description="Native object name.")
    properties: dict[str, Any] = Field(
        default_factory=dict,
        description="Exact property payload at time of capture.",
    )
    completeness: MetadataCompleteness = Field(
        default=MetadataCompleteness.COMPLETE,
        description="Completeness of metadata for this object.",
    )


class PropertyDifference(BaseModel):
    """Detailed before-and-after evidence for a specific modified property."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    property_name: str = Field(description="Name of the changed property (e.g. 'is_nullable', 'native_data_type').")
    before_value: Any = Field(description="Value in baseline snapshot.")
    after_value: Any = Field(description="Value in target snapshot.")
    status: PropertyComparisonStatus = Field(
        default=PropertyComparisonStatus.MODIFIED,
        description="Outcome of property evaluation.",
    )
    is_engine_specific: bool = Field(
        default=False,
        description="True if property semantics depend on specific dialect rules.",
    )
