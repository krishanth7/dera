"""DERA Reverse Engineering — Phase 6.3 Graph Builder.

Constructs strongly typed, immutable, validated ForeignKeyGraph instances from Phase 6.1
canonical schema representations, Phase 6.2 structural reconstruction results, or canonical databases.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from dera.metadata.enums import MetadataCompleteness
from dera.metadata.identity import ObjectId
from dera.metadata.models.database import CanonicalDatabase
from dera.metadata.provenance import MetadataProvenance
from dera.reverse_engineering.graph.capabilities import (
    GraphCapabilityProfile,
    assess_graph_capabilities,
)
from dera.reverse_engineering.graph.edges import ColumnPairMapping, ForeignKeyEdge
from dera.reverse_engineering.graph.errors import (
    GraphBuilderError,
    GraphResourceLimitError,
)
from dera.reverse_engineering.graph.limits import GraphResourceLimits
from dera.reverse_engineering.graph.models import (
    ForeignKeyGraph,
    UnresolvedReason,
    UnresolvedReference,
)
from dera.reverse_engineering.graph.nodes import TableNode
from dera.reverse_engineering.graph.ordering import (
    sort_column_pairs,
    sort_foreign_key_edges,
    sort_table_nodes,
    sort_unresolved_references,
)
from dera.reverse_engineering.graph.validation import (
    ValidationMode,
    validate_foreign_key_graph,
)
from dera.reverse_engineering.references import ResolutionStatus

if TYPE_CHECKING:
    from dera.reverse_engineering.reconstruction.models import (
        StructuralReconstructionResult,
    )
    from dera.reverse_engineering.schema import SchemaRepresentation


class ForeignKeyGraphBuilder:
    """Builder for assembling validated, deterministic ForeignKeyGraph instances."""

    def __init__(
        self,
        database_id: ObjectId,
        database_name: str,
        engine: str,
        workspace_id: str | None = None,
        capability_profile: GraphCapabilityProfile | None = None,
        completeness: MetadataCompleteness = MetadataCompleteness.COMPLETE,
        provenance: MetadataProvenance | None = None,
        limits: GraphResourceLimits | None = None,
        mode: ValidationMode = ValidationMode.PERMISSIVE,
    ) -> None:
        self.database_id = database_id
        self.database_name = database_name
        self.engine = engine.lower()
        self.workspace_id = workspace_id or getattr(database_id, "workspace_id", None)
        self.completeness = completeness
        self.limits = limits or GraphResourceLimits()
        self.mode = mode

        if capability_profile is not None:
            self.capability_profile = capability_profile
        else:
            self.capability_profile = assess_graph_capabilities(
                self.engine, completeness=self.completeness
            )

        if provenance is not None:
            self.provenance = provenance
        else:
            self.provenance = MetadataProvenance(
                source_engine=self.engine,
                native_identifier=self.database_name,
                completeness=self.completeness,
            )

        self._nodes: list[TableNode] = []
        self._edges: list[ForeignKeyEdge] = []
        self._unresolved: list[UnresolvedReference] = []
        self._seen_node_ids: set[ObjectId] = set()
        self._seen_edge_ids: set[ObjectId] = set()

    def add_node(self, node: TableNode) -> ForeignKeyGraphBuilder:
        """Register a table node with duplicate detection and resource bounding."""
        if node.object_id in self._seen_node_ids:
            raise GraphBuilderError(f"Duplicate table node ObjectId: {node.object_id}")

        if len(self._nodes) >= self.limits.max_nodes:
            raise GraphResourceLimitError("max_nodes", self.limits.max_nodes, len(self._nodes) + 1)

        self._seen_node_ids.add(node.object_id)
        self._nodes.append(node)
        return self

    def add_edge(self, edge: ForeignKeyEdge) -> ForeignKeyGraphBuilder:
        """Register a foreign key edge with duplicate detection and resource bounding."""
        if edge.object_id in self._seen_edge_ids:
            raise GraphBuilderError(f"Duplicate foreign key edge ObjectId: {edge.object_id}")

        if len(self._edges) >= self.limits.max_edges:
            raise GraphResourceLimitError("max_edges", self.limits.max_edges, len(self._edges) + 1)

        self._seen_edge_ids.add(edge.object_id)
        self._edges.append(edge)
        return self

    def add_unresolved(self, ref: UnresolvedReference) -> ForeignKeyGraphBuilder:
        """Register an unresolved foreign key reference record."""
        self._unresolved.append(ref)
        return self

    def build(self) -> ForeignKeyGraph:
        """Assemble, validate, deterministically sort, and return the immutable ForeignKeyGraph."""
        # Total column pairs check
        total_pairs = sum(len(e.column_pairs) for e in self._edges)
        if total_pairs > self.limits.max_column_pairs:
            raise GraphResourceLimitError(
                "max_column_pairs",
                self.limits.max_column_pairs,
                total_pairs,
            )

        # Apply deterministic sorting
        sorted_nodes = sort_table_nodes(self._nodes)
        sorted_edges = sort_foreign_key_edges(self._edges)
        sorted_unresolved = sort_unresolved_references(self._unresolved)

        # Run validation
        findings = validate_foreign_key_graph(
            nodes=sorted_nodes,
            edges=sorted_edges,
            workspace_id=self.workspace_id,
            mode=self.mode,
        )

        return ForeignKeyGraph(
            contract_version="1.0.0",
            database_id=self.database_id,
            database_name=self.database_name,
            engine=self.engine,
            workspace_id=self.workspace_id,
            nodes=sorted_nodes,
            edges=sorted_edges,
            unresolved_references=sorted_unresolved,
            validation_findings=findings,
            capability_profile=self.capability_profile,
            completeness=self.completeness,
            provenance=self.provenance,
        )

    @classmethod
    def from_canonical(
        cls,
        database: CanonicalDatabase,
        workspace_id: str | None = None,
        limits: GraphResourceLimits | None = None,
        mode: ValidationMode = ValidationMode.PERMISSIVE,
    ) -> ForeignKeyGraph:
        """Build a ForeignKeyGraph directly from a CanonicalDatabase representation."""
        db_id = (
            getattr(database, "object_id", None) or getattr(database, "id", None) or "db_transient"
        )
        ws_id = (
            workspace_id
            or getattr(database, "workspace_id", None)
            or getattr(db_id, "workspace_id", None)
        )
        completeness = getattr(database, "completeness", None) or (
            database.provenance.completeness
            if hasattr(database, "provenance") and database.provenance
            else MetadataCompleteness.COMPLETE
        )
        builder = cls(
            database_id=db_id,
            database_name=database.name,
            engine=database.engine,
            workspace_id=ws_id,
            completeness=completeness,
            provenance=database.provenance,
            limits=limits,
            mode=mode,
        )

        tables = (
            database.all_tables()
            if hasattr(database, "all_tables")
            else getattr(database, "tables", ())
        )

        # Step 1: Register table nodes
        for table in tables:
            tbl_id = getattr(table, "object_id", None) or getattr(table, "id", None)
            ns_id = getattr(table, "namespace_id", None) or getattr(table, "schema_id", None)
            pk_cols: tuple[str, ...] = ()
            if table.primary_key:
                pk_cols = tuple(
                    getattr(table.primary_key, "columns", None)
                    or getattr(table.primary_key, "column_names", ())
                )

            node = TableNode(
                object_id=tbl_id,
                namespace_id=ns_id,
                native_name=table.name,
                namespace_name=table.schema_name or "public",
                table_type=table.table_type,
                column_count=len(table.columns),
                primary_key_columns=pk_cols,
                completeness=getattr(table, "completeness", None)
                or getattr(table.provenance, "completeness", MetadataCompleteness.COMPLETE),
                native_attributes=getattr(table, "extra_metadata", {}),
                provenance=table.provenance,
            )
            builder.add_node(node)

        # Lookup table nodes by (namespace.lower(), name.lower())
        table_lookup: dict[tuple[str, str], TableNode] = {
            (n.namespace_name.lower(), n.native_name.lower()): n for n in builder._nodes
        }
        # Also lookup by table ID
        table_id_lookup: dict[ObjectId, TableNode] = {n.object_id: n for n in builder._nodes}

        # Step 2: Register foreign key edges and unresolved references
        for table in tables:
            tbl_id = getattr(table, "object_id", None) or getattr(table, "id", None)
            src_node = table_id_lookup.get(tbl_id)
            if src_node is None:
                continue

            for fk in table.foreign_keys:
                fk_id = getattr(fk, "object_id", None) or getattr(fk, "id", None)
                src_cols = tuple(
                    getattr(fk, "declared_source_columns", None)
                    or getattr(fk, "source_columns", None)
                    or getattr(fk, "column_names", None)
                    or ()
                )
                ref_cols = tuple(
                    getattr(fk, "declared_referenced_columns", None)
                    or getattr(fk, "referenced_columns", None)
                    or getattr(fk, "referenced_column_names", None)
                    or ()
                )

                # Validate column mapping lengths
                if len(src_cols) != len(ref_cols) or len(src_cols) == 0:
                    builder.add_unresolved(
                        UnresolvedReference(
                            foreign_key_id=fk_id,
                            native_name=fk.name,
                            source_table_id=tbl_id,
                            source_table_name=table.name,
                            source_namespace=src_node.namespace_name,
                            referenced_table_name=fk.referenced_table_name,
                            referenced_namespace=getattr(fk, "referenced_schema_name", None)
                            or "public",
                            declared_source_columns=src_cols,
                            declared_referenced_columns=ref_cols,
                            reason=UnresolvedReason.INVALID_METADATA,
                            details=(
                                f"Mismatched composite foreign key column counts: "
                                f"{len(src_cols)} source columns vs {len(ref_cols)} referenced columns."
                            ),
                            provenance=fk.provenance,
                        )
                    )
                    continue

                # Build ColumnPairMappings
                column_pairs_list: list[ColumnPairMapping] = []
                for idx, (src_c, ref_c) in enumerate(zip(src_cols, ref_cols, strict=True)):
                    column_pairs_list.append(
                        ColumnPairMapping(
                            source_column_name=src_c,
                            referenced_column_name=ref_c,
                            ordinal_position=idx + 1,
                        )
                    )
                column_pairs = sort_column_pairs(column_pairs_list)

                # Resolve referenced table node
                ref_ns = getattr(fk, "referenced_schema_name", None) or "public"
                ref_tbl_name = fk.referenced_table_name
                ref_node: TableNode | None = None

                ref_tbl_id = getattr(fk, "referenced_table_id", None)
                if ref_tbl_id and ref_tbl_id in table_id_lookup:
                    ref_node = table_id_lookup[ref_tbl_id]
                else:
                    ref_node = table_lookup.get((ref_ns.lower(), ref_tbl_name.lower()))

                if ref_node is None:
                    # Target table is missing or outside metadata scope
                    reason = UnresolvedReason.REFERENCED_TABLE_NOT_FOUND
                    tbl_comp = getattr(table, "completeness", None) or getattr(
                        table.provenance, "completeness", None
                    )
                    if tbl_comp == MetadataCompleteness.RESTRICTED:
                        reason = UnresolvedReason.METADATA_RESTRICTED

                    builder.add_unresolved(
                        UnresolvedReference(
                            foreign_key_id=fk_id,
                            native_name=fk.name,
                            source_table_id=tbl_id,
                            source_table_name=table.name,
                            source_namespace=src_node.namespace_name,
                            referenced_table_name=ref_tbl_name,
                            referenced_namespace=ref_ns,
                            declared_source_columns=src_cols,
                            declared_referenced_columns=ref_cols,
                            reason=reason,
                            details=(
                                f"Referenced table '{ref_ns}.{ref_tbl_name}' could not be resolved "
                                f"among registered table nodes."
                            ),
                            provenance=fk.provenance,
                        )
                    )
                    # Still create edge with referenced_table_id=None to preserve constraint declaration
                    edge = ForeignKeyEdge(
                        object_id=fk_id,
                        native_name=fk.name,
                        source_table_id=tbl_id,
                        referenced_table_id=None,
                        source_namespace=src_node.namespace_name,
                        source_table_name=table.name,
                        referenced_namespace=ref_ns,
                        referenced_table_name=ref_tbl_name,
                        column_pairs=column_pairs,
                        on_delete=fk.on_delete,
                        on_update=fk.on_update,
                        match_type=getattr(fk, "match_type", None),
                        is_deferrable=getattr(fk, "is_deferrable", False),
                        is_enforced=getattr(fk, "is_enforced", True),
                        is_composite=len(column_pairs) > 1,
                        is_self_referencing=False,
                        is_cross_namespace=src_node.namespace_name.lower() != ref_ns.lower(),
                        resolution_status=ResolutionStatus.MISSING,
                        provenance=fk.provenance,
                        extra_metadata=getattr(fk, "extra_metadata", {}),
                    )
                    builder.add_edge(edge)
                else:
                    is_self = src_node.object_id == ref_node.object_id
                    is_cross = src_node.namespace_name.lower() != ref_node.namespace_name.lower()

                    edge = ForeignKeyEdge(
                        object_id=fk_id,
                        native_name=fk.name,
                        source_table_id=tbl_id,
                        referenced_table_id=ref_node.object_id,
                        source_namespace=src_node.namespace_name,
                        source_table_name=table.name,
                        referenced_namespace=ref_node.namespace_name,
                        referenced_table_name=ref_node.native_name,
                        column_pairs=column_pairs,
                        on_delete=fk.on_delete,
                        on_update=fk.on_update,
                        match_type=getattr(fk, "match_type", None),
                        is_deferrable=getattr(fk, "is_deferrable", False),
                        is_enforced=getattr(fk, "is_enforced", True),
                        is_composite=len(column_pairs) > 1,
                        is_self_referencing=is_self,
                        is_cross_namespace=is_cross,
                        resolution_status=ResolutionStatus.RESOLVED,
                        provenance=fk.provenance,
                        extra_metadata=getattr(fk, "extra_metadata", {}),
                    )
                    builder.add_edge(edge)

        return builder.build()

    @classmethod
    def from_reconstruction(
        cls,
        result: StructuralReconstructionResult,
        workspace_id: str | None = None,
        limits: GraphResourceLimits | None = None,
        mode: ValidationMode = ValidationMode.PERMISSIVE,
    ) -> ForeignKeyGraph:
        """Build a ForeignKeyGraph from a Phase 6.2 StructuralReconstructionResult."""
        first_table = result.tables[0] if result.tables else None
        db_id = first_table.object_id if first_table else ObjectId.create_transient()
        eng = result.engine

        builder = cls(
            database_id=db_id,
            database_name=result.database_name,
            engine=eng,
            workspace_id=workspace_id,
            limits=limits,
            mode=mode,
        )

        # Register table nodes
        for tbl in result.tables:
            pk_cols: tuple[str, ...] = ()
            if tbl.primary_key:
                pk_cols = tuple(tbl.primary_key.column_names)

            node = TableNode(
                object_id=tbl.object_id,
                native_name=tbl.native_name,
                namespace_name=tbl.namespace or "public",
                table_type=tbl.table_type,
                column_count=len(tbl.columns),
                primary_key_columns=pk_cols,
                completeness=tbl.completeness,
                native_attributes=tbl.native_attributes,
                provenance=tbl.provenance,
            )
            builder.add_node(node)

        table_id_lookup = {n.object_id: n for n in builder._nodes}
        table_lookup = {
            (n.namespace_name.lower(), n.native_name.lower()): n for n in builder._nodes
        }

        for tbl in result.tables:
            src_node = table_id_lookup.get(tbl.object_id)
            if not src_node:
                continue

            for fk in tbl.foreign_keys:
                src_cols = tuple(fk.source_column_names)
                ref_cols = tuple(fk.referenced_column_names)

                if len(src_cols) != len(ref_cols) or len(src_cols) == 0:
                    builder.add_unresolved(
                        UnresolvedReference(
                            foreign_key_id=fk.object_id,
                            native_name=fk.native_name or "unnamed_fk",
                            source_table_id=tbl.object_id,
                            source_table_name=tbl.native_name,
                            source_namespace=src_node.namespace_name,
                            referenced_table_name=fk.referenced_table_name,
                            referenced_namespace=fk.referenced_namespace or "public",
                            declared_source_columns=src_cols,
                            declared_referenced_columns=ref_cols,
                            reason=UnresolvedReason.INVALID_METADATA,
                            details="Mismatched composite foreign key column counts.",
                            provenance=fk.provenance,
                        )
                    )
                    continue

                column_pairs_list: list[ColumnPairMapping] = []
                for idx, (sc, rc) in enumerate(zip(src_cols, ref_cols, strict=True)):
                    column_pairs_list.append(
                        ColumnPairMapping(
                            source_column_name=sc,
                            referenced_column_name=rc,
                            ordinal_position=idx + 1,
                        )
                    )
                column_pairs = sort_column_pairs(column_pairs_list)

                ref_ns = fk.referenced_namespace or "public"
                ref_tbl_name = fk.referenced_table_name
                ref_node: TableNode | None = None

                if fk.referenced_table_id and fk.referenced_table_id in table_id_lookup:
                    ref_node = table_id_lookup[fk.referenced_table_id]
                else:
                    ref_node = table_lookup.get((ref_ns.lower(), ref_tbl_name.lower()))

                if ref_node is None:
                    builder.add_unresolved(
                        UnresolvedReference(
                            foreign_key_id=fk.object_id,
                            native_name=fk.native_name or "unnamed_fk",
                            source_table_id=tbl.object_id,
                            source_table_name=tbl.native_name,
                            source_namespace=src_node.namespace_name,
                            referenced_table_name=ref_tbl_name,
                            referenced_namespace=ref_ns,
                            declared_source_columns=src_cols,
                            declared_referenced_columns=ref_cols,
                            reason=UnresolvedReason.REFERENCED_TABLE_NOT_FOUND,
                            details=f"Referenced table '{ref_ns}.{ref_tbl_name}' could not be resolved.",
                            provenance=fk.provenance,
                        )
                    )
                    edge = ForeignKeyEdge(
                        object_id=fk.object_id,
                        native_name=fk.native_name or "unnamed_fk",
                        source_table_id=tbl.object_id,
                        referenced_table_id=None,
                        source_namespace=src_node.namespace_name,
                        source_table_name=tbl.native_name,
                        referenced_namespace=ref_ns,
                        referenced_table_name=ref_tbl_name,
                        column_pairs=column_pairs,
                        on_delete=fk.on_delete,
                        on_update=fk.on_update,
                        match_type=fk.match_type,
                        is_deferrable=bool(fk.deferrability),
                        is_enforced=True,
                        is_composite=len(column_pairs) > 1,
                        is_self_referencing=False,
                        is_cross_namespace=src_node.namespace_name.lower() != ref_ns.lower(),
                        resolution_status=ResolutionStatus.MISSING,
                        provenance=fk.provenance,
                    )
                    builder.add_edge(edge)
                else:
                    is_self = src_node.object_id == ref_node.object_id
                    is_cross = src_node.namespace_name.lower() != ref_node.namespace_name.lower()

                    edge = ForeignKeyEdge(
                        object_id=fk.object_id,
                        native_name=fk.native_name or "unnamed_fk",
                        source_table_id=tbl.object_id,
                        referenced_table_id=ref_node.object_id,
                        source_namespace=src_node.namespace_name,
                        source_table_name=tbl.native_name,
                        referenced_namespace=ref_node.namespace_name,
                        referenced_table_name=ref_node.native_name,
                        column_pairs=column_pairs,
                        on_delete=fk.on_delete,
                        on_update=fk.on_update,
                        match_type=fk.match_type,
                        is_deferrable=bool(fk.deferrability),
                        is_enforced=True,
                        is_composite=len(column_pairs) > 1,
                        is_self_referencing=is_self,
                        is_cross_namespace=is_cross,
                        resolution_status=ResolutionStatus.RESOLVED,
                        provenance=fk.provenance,
                    )
                    builder.add_edge(edge)

        return builder.build()

    @classmethod
    def from_schema(
        cls,
        schema: SchemaRepresentation,
        workspace_id: str | None = None,
        limits: GraphResourceLimits | None = None,
        mode: ValidationMode = ValidationMode.PERMISSIVE,
    ) -> ForeignKeyGraph:
        """Build a ForeignKeyGraph from a Phase 6.1 SchemaRepresentation."""
        return cls.from_canonical(
            database=schema.database,
            workspace_id=workspace_id or getattr(schema, "workspace_id", None),
            limits=limits,
            mode=mode,
        )
