"""DERA Connectors — Typed Connector Capability Model.

Defines the capability registry, support status taxonomy, and discovery contracts
used by all DERA database connector implementations.
"""

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from dera_connectors.engine import DatabaseEngine


class ConnectorCapability(StrEnum):
    """Discrete metadata inspection operations supported across connector implementations."""

    SCHEMA_ENUMERATION = "schema_enumeration"
    TABLE_ENUMERATION = "table_enumeration"
    COLUMN_INSPECTION = "column_inspection"
    PRIMARY_KEY_INSPECTION = "primary_key_inspection"
    FOREIGN_KEY_INSPECTION = "foreign_key_inspection"
    UNIQUE_CONSTRAINT_INSPECTION = "unique_constraint_inspection"
    CHECK_CONSTRAINT_INSPECTION = "check_constraint_inspection"
    INDEX_INSPECTION = "index_inspection"
    VIEW_INSPECTION = "view_inspection"
    MATERIALIZED_VIEW_INSPECTION = "materialized_view_inspection"
    TRIGGER_INSPECTION = "trigger_inspection"
    SEQUENCE_INSPECTION = "sequence_inspection"
    FUNCTION_INSPECTION = "function_inspection"
    PROCEDURE_INSPECTION = "procedure_inspection"
    COMMENT_INSPECTION = "comment_inspection"
    PARTITION_INSPECTION = "partition_inspection"
    DEPENDENCY_INSPECTION = "dependency_inspection"


class CapabilityStatus(StrEnum):
    """Status indicating availability of a capability for an active connection."""

    SUPPORTED = "supported"
    UNSUPPORTED = "unsupported"
    RESTRICTED = "restricted"
    UNKNOWN = "unknown"


class CapabilitySupport(BaseModel):
    """Detailed support metadata for a discrete connector capability."""

    model_config = ConfigDict(frozen=True)

    capability: ConnectorCapability = Field(
        ...,
        description="The connector capability being described.",
    )
    status: CapabilityStatus = Field(
        ...,
        description="Support status (supported, unsupported, restricted, or unknown).",
    )
    reason: str | None = Field(
        default=None,
        description="Explanation when capability is unsupported or restricted.",
    )
    version_introduced: str | None = Field(
        default=None,
        description="Server version where capability became available if known.",
    )
    requires_permission: str | None = Field(
        default=None,
        description="Database role or grant required to access this metadata.",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional capability-specific metadata.",
    )


class ConnectorCapabilities(BaseModel):
    """Complete collection of capabilities reported by a database connector."""

    model_config = ConfigDict(frozen=True)

    engine: DatabaseEngine = Field(
        ...,
        description="Database engine associated with this capability profile.",
    )
    capabilities: dict[ConnectorCapability, CapabilitySupport] = Field(
        default_factory=dict,
        description="Mapping of capability identifiers to support declarations.",
    )

    def is_supported(self, capability: ConnectorCapability) -> bool:
        """Return True if capability is explicitly supported and not restricted."""
        support = self.capabilities.get(capability)
        return support is not None and support.status == CapabilityStatus.SUPPORTED

    def get_status(self, capability: ConnectorCapability) -> CapabilityStatus:
        """Return status for a given capability, defaulting to UNKNOWN if omitted."""
        support = self.capabilities.get(capability)
        return support.status if support is not None else CapabilityStatus.UNKNOWN

    def supported_capabilities(self) -> list[ConnectorCapability]:
        """Return a sorted list of all supported capabilities."""
        return sorted(
            [
                cap
                for cap, sup in self.capabilities.items()
                if sup.status == CapabilityStatus.SUPPORTED
            ],
            key=lambda c: c.value,
        )

    def unsupported_capabilities(self) -> list[ConnectorCapability]:
        """Return a sorted list of unsupported capabilities."""
        return sorted(
            [
                cap
                for cap, sup in self.capabilities.items()
                if sup.status == CapabilityStatus.UNSUPPORTED
            ],
            key=lambda c: c.value,
        )

    def restricted_capabilities(self) -> list[ConnectorCapability]:
        """Return a sorted list of restricted capabilities (e.g. insufficient privileges)."""
        return sorted(
            [
                cap
                for cap, sup in self.capabilities.items()
                if sup.status == CapabilityStatus.RESTRICTED
            ],
            key=lambda c: c.value,
        )
