"""DERA Comparison — Phase 9.1 Namespace Comparator.

Detects added, removed, and retained schema namespaces between snapshots.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from dera.comparison.enums import ComparisonChangeType, ComparisonObjectType
from dera.comparison.evidence import ObjectEvidence
from dera.comparison.models import SchemaChange

if TYPE_CHECKING:
    from dera.comparison.models import ComparisonConfig
    from dera.reverse_engineering.snapshots.models import SchemaSnapshot


class NamespaceComparator:
    """Compares namespaces across schema snapshots."""

    @staticmethod
    def compare(
        baseline: SchemaSnapshot,
        target: SchemaSnapshot,
        config: ComparisonConfig,
    ) -> list[SchemaChange]:
        """Produce SchemaChange records for namespace differences."""
        changes: list[SchemaChange] = []
        b_ns = set(baseline.payload.namespaces)
        t_ns = set(target.payload.namespaces)

        # Apply namespace filters if configured
        if config.included_namespaces:
            allowed = set(config.included_namespaces)
            b_ns = b_ns.intersection(allowed)
            t_ns = t_ns.intersection(allowed)

        if config.excluded_namespaces:
            disallowed = set(config.excluded_namespaces)
            b_ns = b_ns.difference(disallowed)
            t_ns = t_ns.difference(disallowed)

        # Removed namespaces
        for ns in sorted(b_ns - t_ns):
            obj_id = f"dera:namespace:{baseline.payload.engine}:{ns}"
            before_ev = ObjectEvidence(
                snapshot_id=baseline.snapshot_id,
                object_id=obj_id,
                namespace=ns,
                name=ns,
                properties={"namespace": ns},
                completeness=baseline.payload.completeness,
            )
            changes.append(
                SchemaChange.create(
                    change_type=ComparisonChangeType.REMOVED,
                    object_type=ComparisonObjectType.NAMESPACE,
                    canonical_id=obj_id,
                    namespace=ns,
                    name=ns,
                    engine=baseline.payload.engine,
                    before_evidence=before_ev,
                    after_evidence=None,
                    metadata_completeness=baseline.payload.completeness,
                )
            )

        # Added namespaces
        for ns in sorted(t_ns - b_ns):
            obj_id = f"dera:namespace:{target.payload.engine}:{ns}"
            after_ev = ObjectEvidence(
                snapshot_id=target.snapshot_id,
                object_id=obj_id,
                namespace=ns,
                name=ns,
                properties={"namespace": ns},
                completeness=target.payload.completeness,
            )
            changes.append(
                SchemaChange.create(
                    change_type=ComparisonChangeType.ADDED,
                    object_type=ComparisonObjectType.NAMESPACE,
                    canonical_id=obj_id,
                    namespace=ns,
                    name=ns,
                    engine=target.payload.engine,
                    before_evidence=None,
                    after_evidence=after_ev,
                    metadata_completeness=target.payload.completeness,
                )
            )

        return changes
