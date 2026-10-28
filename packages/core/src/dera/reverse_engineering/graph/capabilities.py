"""DERA Reverse Engineering — Phase 6.3 Graph Capability Awareness.

Assesses dialect-specific foreign key capabilities and catalog inspection completeness
across PostgreSQL, SQLite, MySQL, and MariaDB.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from dera.metadata.enums import MetadataCompleteness
from dera.reverse_engineering.capabilities import CapabilityState


class GraphCapabilityProfile(BaseModel):
    """Dialect capability profile for foreign key relationship graph construction."""

    model_config = ConfigDict(frozen=True)

    engine: str = Field(
        ...,
        description="Database engine type (e.g. postgresql, sqlite, mysql, mariadb).",
    )
    overall_completeness: MetadataCompleteness = Field(
        default=MetadataCompleteness.COMPLETE,
        description="Overall metadata completeness assessment for foreign key relationships.",
    )
    foreign_keys_state: CapabilityState = Field(
        default=CapabilityState.SUPPORTED,
        description="Capability state of foreign key constraint catalog inspection.",
    )
    supports_composite_keys: bool = Field(
        default=True,
        description="True if engine natively supports multi-column foreign key constraints.",
    )
    supports_deferrable: bool = Field(
        default=False,
        description="True if engine supports DEFERRABLE foreign key evaluation (e.g. PostgreSQL, SQLite).",
    )
    supports_cross_schema_fk: bool = Field(
        default=False,
        description="True if engine natively supports foreign keys referencing other schemas/databases.",
    )
    supports_match_types: bool = Field(
        default=False,
        description="True if engine supports MATCH FULL/PARTIAL/SIMPLE syntax in foreign keys.",
    )
    is_enforcement_guaranteed: bool = Field(
        default=True,
        description="False for engines where FK declarations exist without guaranteed runtime enforcement (e.g. SQLite default).",
    )
    notes: tuple[str, ...] = Field(
        default_factory=tuple,
        description="Engine-specific referential characteristics and limitations.",
    )


def assess_graph_capabilities(
    engine: str,
    completeness: MetadataCompleteness = MetadataCompleteness.COMPLETE,
    extra_capabilities: dict[str, Any] | None = None,
) -> GraphCapabilityProfile:
    """Assess and return the graph capability profile for the target engine."""
    eng_str = str(engine).lower()
    notes: list[str] = []

    if "postgres" in eng_str:
        return GraphCapabilityProfile(
            engine="postgresql",
            overall_completeness=completeness,
            foreign_keys_state=CapabilityState.SUPPORTED,
            supports_composite_keys=True,
            supports_deferrable=True,
            supports_cross_schema_fk=True,
            supports_match_types=True,
            is_enforcement_guaranteed=True,
            notes=("Full standard SQL referential actions and deferrability support.",),
        )

    if "sqlite" in eng_str:
        notes.append("SQLite foreign key declarations do not imply enforcement unless PRAGMA foreign_keys = ON.")
        notes.append("SQLite foreign keys cannot span attached databases.")
        return GraphCapabilityProfile(
            engine="sqlite",
            overall_completeness=completeness,
            foreign_keys_state=CapabilityState.SUPPORTED,
            supports_composite_keys=True,
            supports_deferrable=True,
            supports_cross_schema_fk=False,
            supports_match_types=False,
            is_enforcement_guaranteed=False,
            notes=tuple(notes),
        )

    if "mariadb" in eng_str:
        notes.append("MariaDB referential enforcement is storage-engine dependent (InnoDB/Aria/RocksDB).")
        return GraphCapabilityProfile(
            engine="mariadb",
            overall_completeness=completeness,
            foreign_keys_state=CapabilityState.SUPPORTED,
            supports_composite_keys=True,
            supports_deferrable=False,
            supports_cross_schema_fk=True,
            supports_match_types=False,
            is_enforcement_guaranteed=True,
            notes=tuple(notes),
        )

    if "mysql" in eng_str:
        notes.append("MySQL foreign key enforcement depends on InnoDB; MyISAM tables silently ignore foreign keys.")
        return GraphCapabilityProfile(
            engine="mysql",
            overall_completeness=completeness,
            foreign_keys_state=CapabilityState.SUPPORTED,
            supports_composite_keys=True,
            supports_deferrable=False,
            supports_cross_schema_fk=True,
            supports_match_types=False,
            is_enforcement_guaranteed=True,
            notes=tuple(notes),
        )

    return GraphCapabilityProfile(
        engine=eng_str,
        overall_completeness=completeness,
        foreign_keys_state=CapabilityState.UNKNOWN,
        supports_composite_keys=True,
        supports_deferrable=False,
        supports_cross_schema_fk=False,
        supports_match_types=False,
        is_enforcement_guaranteed=True,
        notes=("Generic SQL catalog capability profile.",),
    )
