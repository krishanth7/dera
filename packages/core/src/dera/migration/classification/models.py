"""DERA Migration — Phase 9.2 Change Classification Models.

Enriches Phase 9.1 SchemaChange records with structural category,
backward compatibility ratings, and affected schema dimensions.
"""

from __future__ import annotations

from typing import Any
from pydantic import BaseModel, ConfigDict, Field

from dera.comparison.enums import ComparisonChangeType, ComparisonObjectType
from dera.comparison.models import SchemaChange
from dera.migration.enums import (
    CompatibilityLevel,
    StructuralChangeCategory,
)


class ClassifiedChange(BaseModel):
    """Enriched schema change record classified for migration analysis."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    source_change_id: str = Field(description="Referenced SchemaChange change_id.")
    source_fingerprint: str = Field(description="Fingerprint of the source SchemaChange.")
    object_type: ComparisonObjectType = Field(description="Type of schema object.")
    change_type: ComparisonChangeType = Field(description="Raw Phase 9.1 change type.")
    category: StructuralChangeCategory = Field(description="High-level structural category.")
    canonical_id: str = Field(description="Canonical ObjectId of the object.")
    namespace: str = Field(description="Namespace / schema name.")
    name: str = Field(description="Native object name.")
    parent_name: str | None = Field(default=None, description="Parent table name if child object.")
    compatibility: CompatibilityLevel = Field(
        description="Assessed backward compatibility level.",
    )
    is_potentially_breaking: bool = Field(
        description="True if change may disrupt existing queries, consumers, or data.",
    )
    compatibility_rationale: str = Field(
        description="Clear, explainable rationale for the compatibility rating.",
    )
    changed_properties: tuple[str, ...] = Field(
        default_factory=tuple,
        description="List of specific properties changed.",
    )
