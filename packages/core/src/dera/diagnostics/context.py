"""DERA Diagnostics — Evaluation Context and Configuration.

Provides immutable evaluation contexts encapsulating canonical schema representations,
snapshots, graph topologies, capability profiles, and resource constraints.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from dera.diagnostics.enums import RuleCategory

if TYPE_CHECKING:
    from dera.reverse_engineering.capabilities import SchemaCapabilityProfile
    from dera.reverse_engineering.dependencies.models import DependencyAnalysisResult
    from dera.reverse_engineering.graph.models import ForeignKeyGraph
    from dera.reverse_engineering.schema import SchemaRepresentation
    from dera.reverse_engineering.snapshots.models import SchemaSnapshot


@dataclass(frozen=True)
class DiagnosticResourceLimits:
    """Configurable resource limits bounding diagnostic evaluation."""

    max_objects: int = 100_000
    max_edges: int = 100_000
    max_findings: int = 10_000
    timeout_seconds: float = 60.0

    def __post_init__(self) -> None:
        if self.max_objects <= 0:
            raise ValueError("max_objects must be strictly positive.")
        if self.max_edges <= 0:
            raise ValueError("max_edges must be strictly positive.")
        if self.max_findings <= 0:
            raise ValueError("max_findings must be strictly positive.")
        if self.timeout_seconds <= 0.0:
            raise ValueError("timeout_seconds must be strictly positive.")


@dataclass(frozen=True)
class DiagnosticEngineConfig:
    """Execution options governing diagnostic rule selection and bounds."""

    enabled_rule_ids: frozenset[str] | None = None
    disabled_rule_ids: frozenset[str] = field(default_factory=frozenset)
    included_categories: frozenset[RuleCategory] | None = None
    excluded_categories: frozenset[RuleCategory] = field(default_factory=frozenset)
    rule_thresholds: dict[str, Any] = field(default_factory=dict)
    suppressions: tuple[Any, ...] = ()
    severity_overrides: tuple[Any, ...] = ()
    limits: DiagnosticResourceLimits = field(default_factory=DiagnosticResourceLimits)

    def to_canonical_dict(self) -> dict[str, Any]:
        """Produces a deterministic configuration dictionary for fingerprinting."""
        return {
            "enabled_rule_ids": sorted(list(self.enabled_rule_ids))
            if self.enabled_rule_ids is not None
            else None,
            "disabled_rule_ids": sorted(list(self.disabled_rule_ids)),
            "included_categories": sorted([c.value for c in self.included_categories])
            if self.included_categories is not None
            else None,
            "excluded_categories": sorted([c.value for c in self.excluded_categories]),
            "rule_thresholds": dict(sorted(self.rule_thresholds.items())),
            "suppressions": [
                s.to_canonical_dict() if hasattr(s, "to_canonical_dict") else str(s)
                for s in self.suppressions
            ],
            "severity_overrides": [
                o.to_canonical_dict() if hasattr(o, "to_canonical_dict") else str(o)
                for o in self.severity_overrides
            ],
            "limits": {
                "max_objects": self.limits.max_objects,
                "max_edges": self.limits.max_edges,
                "max_findings": self.limits.max_findings,
                "timeout_seconds": self.limits.timeout_seconds,
            },
        }


@dataclass(frozen=True)
class DiagnosticContext:
    """Immutable diagnostic evaluation context passed to rules."""

    schema: SchemaRepresentation | None = None
    snapshot: SchemaSnapshot | None = None
    snapshot_id: str | None = None
    graph: ForeignKeyGraph | None = None
    dependencies: DependencyAnalysisResult | None = None
    capabilities: SchemaCapabilityProfile | None = None
    config: DiagnosticEngineConfig = field(default_factory=DiagnosticEngineConfig)
    source_engine: str = "unknown"
    completeness: Any = "COMPLETE"

    def __post_init__(self) -> None:
        # Determine source_engine and completeness from schema or snapshot if available
        if self.schema is not None:
            if hasattr(self.schema, "provenance") and self.schema.provenance is not None:
                if self.source_engine == "unknown":
                    object.__setattr__(self, "source_engine", self.schema.provenance.source_engine)
                object.__setattr__(self, "completeness", self.schema.provenance.completeness)
        elif self.snapshot is not None:
            if hasattr(self.snapshot, "provenance") and self.snapshot.provenance is not None:
                if self.source_engine == "unknown":
                    object.__setattr__(
                        self, "source_engine", self.snapshot.provenance.source_engine
                    )
                object.__setattr__(self, "completeness", self.snapshot.provenance.completeness)
            if self.snapshot_id is None and hasattr(self.snapshot, "snapshot_id"):
                object.__setattr__(self, "snapshot_id", self.snapshot.snapshot_id)
