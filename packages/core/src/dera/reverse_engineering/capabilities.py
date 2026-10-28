"""DERA Reverse Engineering — Phase 6.1 Capability Awareness.

Integrates Phase 5 capability states and completeness assessments into the schema
representation layer. Tracks supported, unsupported, restricted, and unknown engine
capabilities without fabricating absent metadata.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from dera.metadata.capabilities import assess_engine_metadata_completeness
from dera.metadata.enums import MetadataCompleteness
from dera.metadata.models.database import CanonicalDatabase


class CapabilityState(StrEnum):
    """Fine-grained capability state for a database feature in the schema representation.

    - SUPPORTED: The engine natively supports the catalog feature and metadata was extracted.
    - UNSUPPORTED: The engine does not provide this capability (e.g. stored procedures in SQLite).
    - RESTRICTED: The engine supports this feature but the inspection account lacks catalog permissions.
    - UNKNOWN: Capability status could not be affirmatively determined.
    """

    SUPPORTED = "supported"
    UNSUPPORTED = "unsupported"
    RESTRICTED = "restricted"
    UNKNOWN = "unknown"


# Standard capability feature keys across supported engines
STANDARD_SCHEMA_FEATURES: tuple[str, ...] = (
    "namespaces",
    "tables",
    "columns",
    "primary_keys",
    "foreign_keys",
    "unique_constraints",
    "check_constraints",
    "indexes",
    "views",
    "triggers",
    "expression_indexes",
    "generated_columns",
    "identity_columns",
    "comments",
)


class SchemaCapabilityProfile(BaseModel):
    """Summary of engine catalog capabilities and inspection completeness."""

    model_config = ConfigDict(frozen=True)

    engine: str = Field(
        ...,
        description="Database engine type (e.g. 'postgresql', 'sqlite', 'mysql', 'mariadb').",
    )
    overall_completeness: MetadataCompleteness = Field(
        default=MetadataCompleteness.COMPLETE,
        description="Aggregated completeness classification for the schema.",
    )
    features: dict[str, CapabilityState] = Field(
        default_factory=dict,
        description="Mapping of standard feature name to capability state.",
    )

    @property
    def has_restricted_metadata(self) -> bool:
        """True if any catalog feature was restricted during inspection."""
        return any(state == CapabilityState.RESTRICTED for state in self.features.values())

    @property
    def has_unsupported_features(self) -> bool:
        """True if any catalog feature is unsupported by this engine."""
        return any(state == CapabilityState.UNSUPPORTED for state in self.features.values())

    def is_feature_supported(self, feature: str) -> bool:
        """Check whether a specific catalog feature is supported."""
        return self.features.get(feature) == CapabilityState.SUPPORTED


def assess_schema_capabilities(
    engine: str,
    database: CanonicalDatabase,
    capabilities: dict[str, Any] | None = None,
) -> SchemaCapabilityProfile:
    """Construct a SchemaCapabilityProfile for an inspected canonical database.

    Evaluates known engine behaviors and connector-reported capabilities.
    """
    clean_engine = engine.strip().lower()
    features: dict[str, CapabilityState] = {}
    is_partial = False
    is_restricted = False

    for feature in STANDARD_SCHEMA_FEATURES:
        completeness = assess_engine_metadata_completeness(clean_engine, feature, capabilities)
        if completeness == MetadataCompleteness.COMPLETE:
            features[feature] = CapabilityState.SUPPORTED
        elif completeness == MetadataCompleteness.PARTIAL:
            features[feature] = CapabilityState.SUPPORTED
            is_partial = True
        elif completeness == MetadataCompleteness.RESTRICTED:
            features[feature] = CapabilityState.RESTRICTED
            is_restricted = True
        elif completeness == MetadataCompleteness.UNSUPPORTED:
            features[feature] = CapabilityState.UNSUPPORTED
        else:
            features[feature] = CapabilityState.UNKNOWN

    # Determine overall completeness
    if is_restricted:
        overall = MetadataCompleteness.RESTRICTED
    elif is_partial:
        overall = MetadataCompleteness.PARTIAL
    else:
        overall = MetadataCompleteness.COMPLETE

    return SchemaCapabilityProfile(
        engine=clean_engine,
        overall_completeness=overall,
        features=features,
    )


__all__ = [
    "CapabilityState",
    "STANDARD_SCHEMA_FEATURES",
    "SchemaCapabilityProfile",
    "assess_schema_capabilities",
]
