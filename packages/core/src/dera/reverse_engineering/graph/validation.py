"""DERA Reverse Engineering — Phase 6.3 Graph Validation.

Implements rigorous integrity, consistency, and referential validation for foreign key
relationship graphs with multi-level diagnostic severity reporting.
"""

from __future__ import annotations

from collections.abc import Iterable
from enum import StrEnum
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, ConfigDict, Field

from dera.metadata.identity import ObjectId
from dera.reverse_engineering.graph.edges import ForeignKeyEdge
from dera.reverse_engineering.graph.errors import GraphValidationError
from dera.reverse_engineering.graph.nodes import TableNode
from dera.reverse_engineering.graph.ordering import sort_validation_findings

if TYPE_CHECKING:
    from dera.reverse_engineering.graph.adjacency import AdjacencyIndex


class ValidationSeverity(StrEnum):
    """Severity classification for graph validation findings."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ValidationMode(StrEnum):
    """Enforcement policy for graph validation."""

    STRICT = "strict"
    PERMISSIVE = "permissive"


class GraphValidationFinding(BaseModel):
    """Immutable diagnostic record produced during graph integrity validation."""

    model_config = ConfigDict(frozen=True)

    code: str = Field(
        ...,
        description="Standardized machine-readable diagnostic code (e.g. FKG_DANGLING_TARGET).",
    )
    severity: ValidationSeverity = Field(
        ...,
        description="Severity level of the diagnostic finding.",
    )
    message: str = Field(
        ...,
        description="Clear, actionable explanation of the structural anomaly.",
    )
    object_id: ObjectId | None = Field(
        default=None,
        description="Primary ObjectId associated with this finding.",
    )
    source_table_id: ObjectId | None = Field(
        default=None,
        description="Source table ObjectId if relevant to the finding.",
    )
    referenced_table_id: ObjectId | None = Field(
        default=None,
        description="Referenced table ObjectId if relevant to the finding.",
    )
    details: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional structured context or diagnostic metrics.",
    )

    def __repr__(self) -> str:
        return f"GraphValidationFinding([{self.severity.value.upper()}] {self.code}: {self.message})"


def validate_foreign_key_graph(
    nodes: Iterable[TableNode],
    edges: Iterable[ForeignKeyEdge],
    adjacency: AdjacencyIndex | None = None,
    workspace_id: str | None = None,
    mode: ValidationMode = ValidationMode.PERMISSIVE,
) -> tuple[GraphValidationFinding, ...]:
    """Validates structural consistency and referential constraints across the graph.

    Checks:
    - Node ObjectId uniqueness.
    - Edge ObjectId uniqueness.
    - Source table node existence for every edge.
    - Referenced table node existence for every resolved edge.
    - Column pair sequence and ordinal completeness.
    - Workspace boundary integrity.
    - Bidirectional adjacency index consistency.

    Raises:
        GraphValidationError: If mode is STRICT and any findings have ERROR severity.
    """
    findings: list[GraphValidationFinding] = []
    node_map: dict[ObjectId, TableNode] = {}
    seen_node_ids: set[ObjectId] = set()

    # 1. Node Validation
    for node in nodes:
        if node.object_id in seen_node_ids:
            findings.append(
                GraphValidationFinding(
                    code="FKG_DUPLICATE_NODE_ID",
                    severity=ValidationSeverity.ERROR,
                    message=f"Duplicate table node ObjectId detected: {node.object_id}",
                    object_id=node.object_id,
                    details={"table_name": node.fully_qualified_name},
                )
            )
        else:
            seen_node_ids.add(node.object_id)
            node_map[node.object_id] = node

        # Workspace check
        if workspace_id and hasattr(node.object_id, "workspace_id"):
            node_ws = getattr(node.object_id, "workspace_id", None)
            if node_ws and node_ws != workspace_id:
                findings.append(
                    GraphValidationFinding(
                        code="FKG_CROSS_WORKSPACE_NODE",
                        severity=ValidationSeverity.ERROR,
                        message=(
                            f"Table node {node.fully_qualified_name} workspace {node_ws} "
                            f"does not match graph workspace {workspace_id}"
                        ),
                        object_id=node.object_id,
                    )
                )

    # 2. Edge Validation
    seen_edge_ids: set[ObjectId] = set()
    for edge in edges:
        if edge.object_id in seen_edge_ids:
            findings.append(
                GraphValidationFinding(
                    code="FKG_DUPLICATE_EDGE_ID",
                    severity=ValidationSeverity.ERROR,
                    message=f"Duplicate foreign key edge ObjectId detected: {edge.object_id}",
                    object_id=edge.object_id,
                    details={"constraint_name": edge.native_name},
                )
            )
        else:
            seen_edge_ids.add(edge.object_id)

        # Source table node existence
        if edge.source_table_id not in node_map:
            findings.append(
                GraphValidationFinding(
                    code="FKG_MISSING_SOURCE_NODE",
                    severity=ValidationSeverity.ERROR,
                    message=(
                        f"Foreign key '{edge.native_name}' declares non-existent source table ID: {edge.source_table_id}"
                    ),
                    object_id=edge.object_id,
                    source_table_id=edge.source_table_id,
                )
            )

        # Referenced table node existence
        if edge.referenced_table_id is not None:
            if edge.referenced_table_id not in node_map:
                findings.append(
                    GraphValidationFinding(
                        code="FKG_DANGLING_TARGET_NODE",
                        severity=ValidationSeverity.ERROR,
                        message=(
                            f"Foreign key '{edge.native_name}' references non-existent parent table ID: {edge.referenced_table_id}"
                        ),
                        object_id=edge.object_id,
                        source_table_id=edge.source_table_id,
                        referenced_table_id=edge.referenced_table_id,
                        details={"referenced_table": edge.referenced_fully_qualified_name},
                    )
                )

        # Column pair integrity
        if not edge.column_pairs:
            findings.append(
                GraphValidationFinding(
                    code="FKG_EMPTY_COLUMN_PAIRS",
                    severity=ValidationSeverity.ERROR,
                    message=f"Foreign key '{edge.native_name}' contains no column pair mappings.",
                    object_id=edge.object_id,
                    source_table_id=edge.source_table_id,
                )
            )
        else:
            ordinals = [p.ordinal_position for p in edge.column_pairs]
            expected_ordinals = list(range(1, len(edge.column_pairs) + 1))
            if ordinals != expected_ordinals:
                findings.append(
                    GraphValidationFinding(
                        code="FKG_INVALID_COLUMN_ORDINALS",
                        severity=ValidationSeverity.WARNING,
                        message=(
                            f"Foreign key '{edge.native_name}' column ordinals {ordinals} do not form "
                            f"contiguous 1..N sequence {expected_ordinals}."
                        ),
                        object_id=edge.object_id,
                        details={"actual_ordinals": ordinals},
                    )
                )

    # 3. Adjacency Consistency Validation
    if adjacency is not None:
        for edge in edges:
            src_edges = adjacency.get_outgoing(edge.source_table_id)
            if edge not in src_edges:
                findings.append(
                    GraphValidationFinding(
                        code="FKG_ADJACENCY_OUTGOING_DESYNC",
                        severity=ValidationSeverity.ERROR,
                        message=f"Edge '{edge.native_name}' missing from outgoing adjacency index of source table.",
                        object_id=edge.object_id,
                        source_table_id=edge.source_table_id,
                    )
                )

            if edge.referenced_table_id is not None and edge.referenced_table_id in node_map:
                ref_edges = adjacency.get_incoming(edge.referenced_table_id)
                if edge not in ref_edges:
                    findings.append(
                        GraphValidationFinding(
                            code="FKG_ADJACENCY_INCOMING_DESYNC",
                            severity=ValidationSeverity.ERROR,
                            message=f"Edge '{edge.native_name}' missing from incoming adjacency index of referenced table.",
                            object_id=edge.object_id,
                            referenced_table_id=edge.referenced_table_id,
                        )
                    )

    sorted_findings = sort_validation_findings(findings)

    if mode == ValidationMode.STRICT:
        errors = [f for f in sorted_findings if f.severity == ValidationSeverity.ERROR]
        if errors:
            raise GraphValidationError(
                f"Graph validation failed in STRICT mode with {len(errors)} error(s): {errors[0].message}"
            )

    return sorted_findings
