"""DERA Canonical Metadata Normalization & Identity — Normalization Pipeline.

Executes deterministic, end-to-end transformation from raw connector metadata reports
(Phase 5.1-5.4) into strongly typed, immutable CanonicalDatabase schema models.
"""

from __future__ import annotations

from typing import Any

from dera.metadata.adapters import (
    MariaDbMetadataAdapter,
    MySqlMetadataAdapter,
    PostgresqlMetadataAdapter,
    SqliteMetadataAdapter,
)
from dera.metadata.capabilities import assess_engine_metadata_completeness
from dera.metadata.enums import (
    ConstraintType,
    ForeignKeyAction,
    GenerationMode,
    IndexType,
    MetadataCompleteness,
    ObjectKind,
    TableType,
    TriggerEvent,
    TriggerTiming,
)
from dera.metadata.errors import (
    InvalidConnectorMetadataError,
)
from dera.metadata.identity import (
    compute_stable_object_id,
    generate_unnamed_constraint_name,
)
from dera.metadata.models import (
    CanonicalColumn,
    CanonicalConstraint,
    CanonicalDatabase,
    CanonicalForeignKey,
    CanonicalIndex,
    CanonicalIndexTerm,
    CanonicalNamespace,
    CanonicalTable,
    CanonicalTrigger,
    CanonicalView,
    ForeignKeyMapping,
)
from dera.metadata.ordering import (
    sort_columns,
    sort_constraints,
    sort_foreign_key_mappings,
    sort_foreign_keys,
    sort_index_terms,
    sort_indexes,
    sort_namespaces,
    sort_tables,
    sort_triggers,
    sort_views,
)
from dera.metadata.provenance import MetadataProvenance
from dera.metadata.validation import validate_canonical_database


def _get_val(obj: Any, key: str, default: Any = None) -> Any:
    """Safely extract field value whether obj is a Pydantic model or dict."""
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


class MetadataNormalizer:
    """Deterministic normalization pipeline converting connector metadata to canonical models."""

    def __init__(
        self,
        engine: str,
        database_name: str = "default",
        server_version: str | None = None,
        workspace_id: str | None = None,
        connection_id: str | None = None,
        connector_version: str = "0.1.0-dev",
        capabilities: dict[str, Any] | None = None,
    ) -> None:
        self.engine = engine.strip().lower()
        self.database_name = database_name.strip()
        self.server_version = server_version
        self.workspace_id = workspace_id
        self.connection_id = connection_id
        self.connector_version = connector_version
        self.capabilities = capabilities or {}

    def _get_adapter(self) -> Any:
        if self.engine in ("postgresql", "postgres", "supabase"):
            return PostgresqlMetadataAdapter
        if self.engine == "sqlite":
            return SqliteMetadataAdapter
        if self.engine == "mysql":
            return MySqlMetadataAdapter
        if self.engine == "mariadb":
            return MariaDbMetadataAdapter
        return PostgresqlMetadataAdapter

    def normalize(self, report: Any) -> CanonicalDatabase:
        """Execute full normalization pipeline on a connector metadata report.

        Accepts either:
        - `DatabaseMetadataReport` instance from `dera_connectors.metadata`
        - Dictionary conforming to connector metadata structure
        """
        adapter = self._get_adapter()

        # Extract collections safely whether report is Pydantic model or dict
        if hasattr(report, "schemas"):
            schemas_in = report.schemas
            tables_in = report.tables
            columns_in = report.columns
            pk_in = report.primary_keys
            fk_in = report.foreign_keys
            unique_in = report.unique_constraints
            check_in = report.check_constraints
            indexes_in = report.indexes
            views_in = report.views
            triggers_in = getattr(report, "triggers", [])
            db_name = getattr(report, "database_name", None) or self.database_name
        elif isinstance(report, dict):
            schemas_in = report.get("schemas", [])
            tables_in = report.get("tables", [])
            columns_in = report.get("columns", [])
            pk_in = report.get("primary_keys", [])
            fk_in = report.get("foreign_keys", [])
            unique_in = report.get("unique_constraints", [])
            check_in = report.get("check_constraints", [])
            indexes_in = report.get("indexes", [])
            views_in = report.get("views", [])
            triggers_in = report.get("triggers", [])
            db_name = report.get("database_name") or self.database_name
        else:
            raise InvalidConnectorMetadataError(
                f"Unsupported report payload type: {type(report).__name__}"
            )

        # 1. Compute Database Object ID
        db_id = compute_stable_object_id(
            engine=self.engine,
            object_kind=ObjectKind.DATABASE,
            native_name=db_name,
            workspace_id=self.workspace_id,
            connection_id=self.connection_id,
        )

        db_provenance = MetadataProvenance(
            source_engine=self.engine,
            source_version=self.server_version,
            connector_version=self.connector_version,
            completeness=MetadataCompleteness.COMPLETE,
            native_identifier=db_name,
            source_location=db_name,
        )

        # 2. Organize Namespaces
        schema_names: set[str] = set()
        for s in schemas_in:
            s_name = _get_val(s, "schema_name") or str(s)
            if s_name:
                schema_names.add(s_name)

        # Fallback to schemas inferred from tables/views if schemas list was empty
        for t in tables_in:
            t_schema = _get_val(t, "schema_name")
            if t_schema:
                schema_names.add(t_schema)

        for v in views_in:
            v_schema = _get_val(v, "schema_name")
            if v_schema:
                schema_names.add(v_schema)

        if not schema_names:
            schema_names.add("main" if self.engine == "sqlite" else "public")

        # 3. Index raw inputs by (schema, table)
        columns_by_table: dict[tuple[str, str], list[Any]] = {}
        for c in columns_in:
            cs = _get_val(c, "schema_name", "") or ""
            ct = _get_val(c, "table_name", "") or ""
            columns_by_table.setdefault((cs.lower(), ct.lower()), []).append(c)

        pk_by_table: dict[tuple[str, str], Any] = {}
        for pk in pk_in:
            pks = _get_val(pk, "schema_name", "") or ""
            pkt = _get_val(pk, "table_name", "") or ""
            pk_by_table[(pks.lower(), pkt.lower())] = pk

        fk_by_table: dict[tuple[str, str], list[Any]] = {}
        for fk in fk_in:
            fks = _get_val(fk, "schema_name", "") or ""
            fkt = _get_val(fk, "table_name", "") or ""
            fk_by_table.setdefault((fks.lower(), fkt.lower()), []).append(fk)

        unique_by_table: dict[tuple[str, str], list[Any]] = {}
        for u in unique_in:
            us = _get_val(u, "schema_name", "") or ""
            ut = _get_val(u, "table_name", "") or ""
            unique_by_table.setdefault((us.lower(), ut.lower()), []).append(u)

        check_by_table: dict[tuple[str, str], list[Any]] = {}
        for ch in check_in:
            chs = _get_val(ch, "schema_name", "") or ""
            cht = _get_val(ch, "table_name", "") or ""
            check_by_table.setdefault((chs.lower(), cht.lower()), []).append(ch)

        indexes_by_table: dict[tuple[str, str], list[Any]] = {}
        for idx in indexes_in:
            is_ = _get_val(idx, "schema_name", "") or ""
            it = _get_val(idx, "table_name", "") or ""
            indexes_by_table.setdefault((is_.lower(), it.lower()), []).append(idx)

        triggers_by_table: dict[tuple[str, str], list[Any]] = {}
        for tr in triggers_in:
            trs = _get_val(tr, "schema_name", "") or ""
            trt = _get_val(tr, "table_name", "") or ""
            triggers_by_table.setdefault((trs.lower(), trt.lower()), []).append(tr)

        views_by_schema: dict[str, list[Any]] = {}
        for v in views_in:
            vs = _get_val(v, "schema_name", "") or ""
            views_by_schema.setdefault(vs.lower(), []).append(v)

        tables_by_schema: dict[str, list[Any]] = {}
        for t in tables_in:
            ts = _get_val(t, "schema_name", "") or ""
            tables_by_schema.setdefault(ts.lower(), []).append(t)

        # 4. Construct Canonical Namespaces
        canonical_namespaces: list[CanonicalNamespace] = []

        for s_name in sorted(schema_names):
            ns_id = compute_stable_object_id(
                engine=self.engine,
                object_kind=ObjectKind.NAMESPACE,
                native_name=s_name,
                parent_id=db_id,
                workspace_id=self.workspace_id,
                connection_id=self.connection_id,
            )

            ns_prov = MetadataProvenance(
                source_engine=self.engine,
                source_version=self.server_version,
                connector_version=self.connector_version,
                completeness=MetadataCompleteness.COMPLETE,
                native_identifier=s_name,
                source_location=f"{db_name}.{s_name}",
            )

            # Build Tables in Namespace
            canonical_tables: list[CanonicalTable] = []
            for t_raw in tables_by_schema.get(s_name.lower(), []):
                t_name = _get_val(t_raw, "table_name", "")
                t_comment = _get_val(t_raw, "comment", None)
                raw_type = str(_get_val(t_raw, "object_type", "TABLE")).upper()

                t_type = TableType.TABLE
                if "SYSTEM" in raw_type:
                    t_type = TableType.SYSTEM_TABLE
                elif "PARTITION" in raw_type:
                    t_type = TableType.PARTITIONED_TABLE

                tbl_id = compute_stable_object_id(
                    engine=self.engine,
                    object_kind=ObjectKind.TABLE,
                    native_name=t_name,
                    namespace=s_name,
                    parent_id=ns_id,
                    workspace_id=self.workspace_id,
                    connection_id=self.connection_id,
                )

                tbl_prov = MetadataProvenance(
                    source_engine=self.engine,
                    source_version=self.server_version,
                    connector_version=self.connector_version,
                    completeness=MetadataCompleteness.COMPLETE,
                    native_identifier=t_name,
                    source_location=f"{s_name}.{t_name}",
                )

                # Process Columns
                canonical_columns: list[CanonicalColumn] = []
                for c_raw in columns_by_table.get((s_name.lower(), t_name.lower()), []):
                    c_name = _get_val(c_raw, "column_name", "")
                    c_pos = int(_get_val(c_raw, "ordinal_position", 1))
                    c_type = _get_val(c_raw, "data_type", "") or ""
                    c_nullable = bool(_get_val(c_raw, "is_nullable", True))
                    c_default = _get_val(c_raw, "default_expression", None)
                    c_identity = bool(_get_val(c_raw, "is_identity", False))
                    c_gen = bool(_get_val(c_raw, "is_generated", False))
                    c_gen_expr = _get_val(c_raw, "generation_expression", None)
                    c_comment = _get_val(c_raw, "comment", None)
                    extra_val = _get_val(c_raw, "extra", "") or _get_val(
                        c_raw, "full_data_type", ""
                    )

                    if hasattr(adapter, "categorize_type"):
                        try:
                            cat_type = adapter.categorize_type(c_type, extra_val)
                        except TypeError:
                            cat_type = adapter.categorize_type(c_type)
                    else:
                        cat_type = adapter.categorize_type(c_type)

                    gen_mode = GenerationMode.STORED if c_gen else GenerationMode.NONE
                    if hasattr(adapter, "parse_generation_mode"):
                        parsed_mode = adapter.parse_generation_mode(extra_val or c_gen_expr)
                        if parsed_mode != GenerationMode.NONE:
                            gen_mode = parsed_mode

                    col_id = compute_stable_object_id(
                        engine=self.engine,
                        object_kind=ObjectKind.COLUMN,
                        native_name=c_name,
                        namespace=s_name,
                        parent_id=tbl_id,
                        workspace_id=self.workspace_id,
                        connection_id=self.connection_id,
                    )

                    col_prov = MetadataProvenance(
                        source_engine=self.engine,
                        source_version=self.server_version,
                        connector_version=self.connector_version,
                        completeness=MetadataCompleteness.COMPLETE,
                        native_identifier=c_name,
                        source_location=f"{s_name}.{t_name}.{c_name}",
                    )

                    canonical_columns.append(
                        CanonicalColumn(
                            id=col_id,
                            parent_table_id=tbl_id,
                            name=c_name,
                            ordinal_position=c_pos,
                            native_data_type=c_type,
                            canonical_type=cat_type,
                            is_nullable=c_nullable,
                            default_expression=c_default,
                            is_identity=c_identity,
                            is_generated=c_gen,
                            generation_mode=gen_mode,
                            generation_expression=c_gen_expr,
                            comment=c_comment,
                            provenance=col_prov,
                        )
                    )

                sorted_columns = sort_columns(canonical_columns)

                # Process Primary Key
                pk_raw = pk_by_table.get((s_name.lower(), t_name.lower()))
                canonical_pk: CanonicalConstraint | None = None
                if pk_raw:
                    pk_name = _get_val(pk_raw, "constraint_name", None) or "PRIMARY"
                    pk_cols = tuple(
                        _get_val(pk_raw, "column_names") or _get_val(pk_raw, "columns") or ()
                    )
                    pk_id = compute_stable_object_id(
                        engine=self.engine,
                        object_kind=ObjectKind.PRIMARY_KEY,
                        native_name=pk_name,
                        namespace=s_name,
                        parent_id=tbl_id,
                        workspace_id=self.workspace_id,
                        connection_id=self.connection_id,
                        terms=pk_cols,
                    )
                    canonical_pk = CanonicalConstraint(
                        id=pk_id,
                        parent_table_id=tbl_id,
                        name=pk_name,
                        constraint_type=ConstraintType.PRIMARY_KEY,
                        columns=pk_cols,
                        provenance=tbl_prov,
                    )

                # Process Unique Constraints
                canonical_unique: list[CanonicalConstraint] = []
                for u_raw in unique_by_table.get((s_name.lower(), t_name.lower()), []):
                    u_name = _get_val(u_raw, "constraint_name", "") or ""
                    u_cols = tuple(
                        _get_val(u_raw, "column_names") or _get_val(u_raw, "columns") or ()
                    )
                    is_synthetic = False
                    if not u_name:
                        u_name = generate_unnamed_constraint_name(t_name, "unique", u_cols)
                        is_synthetic = True

                    u_id = compute_stable_object_id(
                        engine=self.engine,
                        object_kind=ObjectKind.UNIQUE_CONSTRAINT,
                        native_name=u_name,
                        namespace=s_name,
                        parent_id=tbl_id,
                        workspace_id=self.workspace_id,
                        connection_id=self.connection_id,
                        terms=u_cols,
                    )
                    canonical_unique.append(
                        CanonicalConstraint(
                            id=u_id,
                            parent_table_id=tbl_id,
                            name=u_name,
                            constraint_type=ConstraintType.UNIQUE,
                            columns=u_cols,
                            is_synthetic_name=is_synthetic,
                            provenance=tbl_prov,
                        )
                    )

                # Process Check Constraints
                canonical_check: list[CanonicalConstraint] = []
                for ch_raw in check_by_table.get((s_name.lower(), t_name.lower()), []):
                    ch_name = _get_val(ch_raw, "constraint_name", "") or ""
                    ch_expr = _get_val(ch_raw, "check_clause", None)
                    ch_cols = tuple(
                        _get_val(ch_raw, "column_names") or _get_val(ch_raw, "columns") or ()
                    )
                    is_synthetic = False
                    if not ch_name:
                        ch_name = generate_unnamed_constraint_name(
                            t_name, "check", ch_cols or [t_name]
                        )
                        is_synthetic = True

                    ch_id = compute_stable_object_id(
                        engine=self.engine,
                        object_kind=ObjectKind.CHECK_CONSTRAINT,
                        native_name=ch_name,
                        namespace=s_name,
                        parent_id=tbl_id,
                        workspace_id=self.workspace_id,
                        connection_id=self.connection_id,
                        terms=ch_cols,
                    )
                    canonical_check.append(
                        CanonicalConstraint(
                            id=ch_id,
                            parent_table_id=tbl_id,
                            name=ch_name,
                            constraint_type=ConstraintType.CHECK,
                            columns=ch_cols,
                            check_clause=ch_expr,
                            is_synthetic_name=is_synthetic,
                            provenance=tbl_prov,
                        )
                    )

                # Process Foreign Keys
                canonical_fk: list[CanonicalForeignKey] = []
                for fk_raw in fk_by_table.get((s_name.lower(), t_name.lower()), []):
                    fk_name = _get_val(fk_raw, "constraint_name", "") or ""
                    ref_tbl = (
                        _get_val(fk_raw, "referenced_table")
                        or _get_val(fk_raw, "referenced_table_name")
                        or ""
                    )
                    ref_schema = _get_val(fk_raw, "referenced_schema") or _get_val(
                        fk_raw, "referenced_schema_name"
                    )
                    on_up = str(_get_val(fk_raw, "on_update", "NO ACTION")).upper()
                    on_del = str(_get_val(fk_raw, "on_delete", "NO ACTION")).upper()

                    # Extract column mappings
                    mappings: list[ForeignKeyMapping] = []
                    raw_maps = _get_val(fk_raw, "column_mappings", None)
                    if raw_maps:
                        for m in raw_maps:
                            sc = _get_val(m, "source_column", "")
                            tc = _get_val(m, "referenced_column", "")
                            mappings.append(
                                ForeignKeyMapping(source_column=sc, referenced_column=tc)
                            )
                    else:
                        src_cols = tuple(
                            _get_val(fk_raw, "column_names")
                            or _get_val(fk_raw, "source_columns")
                            or ()
                        )
                        ref_cols = tuple(_get_val(fk_raw, "referenced_columns") or ())
                        for sc, tc in zip(src_cols, ref_cols, strict=False):
                            mappings.append(
                                ForeignKeyMapping(source_column=sc, referenced_column=tc)
                            )

                    is_synthetic = False
                    if not fk_name:
                        fk_name = generate_unnamed_constraint_name(
                            t_name, "fk", [m.source_column for m in mappings]
                        )
                        is_synthetic = True

                    fk_id = compute_stable_object_id(
                        engine=self.engine,
                        object_kind=ObjectKind.FOREIGN_KEY,
                        native_name=fk_name,
                        namespace=s_name,
                        parent_id=tbl_id,
                        workspace_id=self.workspace_id,
                        connection_id=self.connection_id,
                        terms=[m.source_column for m in mappings],
                    )

                    act_up = (
                        ForeignKeyAction(on_up)
                        if on_up in ForeignKeyAction.__members__.values()
                        else ForeignKeyAction.NO_ACTION
                    )
                    act_del = (
                        ForeignKeyAction(on_del)
                        if on_del in ForeignKeyAction.__members__.values()
                        else ForeignKeyAction.NO_ACTION
                    )

                    canonical_fk.append(
                        CanonicalForeignKey(
                            id=fk_id,
                            name=fk_name,
                            source_table_id=tbl_id,
                            source_table_name=t_name,
                            referenced_table_name=ref_tbl,
                            referenced_schema=ref_schema,
                            column_mappings=sort_foreign_key_mappings(mappings),
                            on_update=act_up,
                            on_delete=act_del,
                            is_synthetic_name=is_synthetic,
                            provenance=tbl_prov,
                        )
                    )

                # Process Indexes
                canonical_indexes: list[CanonicalIndex] = []
                for idx_raw in indexes_by_table.get((s_name.lower(), t_name.lower()), []):
                    idx_name = _get_val(idx_raw, "index_name", "") or ""
                    is_unq = bool(_get_val(idx_raw, "is_unique", False))
                    is_prim = bool(_get_val(idx_raw, "is_primary", False))
                    idx_type_raw = _get_val(idx_raw, "index_type", "BTREE") or "BTREE"
                    predicate_val = _get_val(idx_raw, "predicate", None)

                    # Index terms
                    terms: list[CanonicalIndexTerm] = []
                    raw_cols = _get_val(idx_raw, "column_names") or _get_val(idx_raw, "columns")
                    if raw_cols:
                        for pos, c in enumerate(raw_cols, start=1):
                            if isinstance(c, str):
                                terms.append(
                                    CanonicalIndexTerm(column_name=c, ordinal_position=pos)
                                )
                            else:
                                c_name_term = _get_val(c, "column_name", None)
                                c_expr = _get_val(c, "expression", None)
                                c_desc = bool(_get_val(c, "is_descending", False))
                                terms.append(
                                    CanonicalIndexTerm(
                                        column_name=c_name_term,
                                        expression=c_expr,
                                        ordinal_position=pos,
                                        is_descending=c_desc,
                                        is_expression=bool(c_expr),
                                    )
                                )

                    term_names = [
                        t.column_name or t.expression or str(i) for i, t in enumerate(terms)
                    ]
                    idx_id = compute_stable_object_id(
                        engine=self.engine,
                        object_kind=ObjectKind.INDEX,
                        native_name=idx_name,
                        namespace=s_name,
                        parent_id=tbl_id,
                        workspace_id=self.workspace_id,
                        connection_id=self.connection_id,
                        terms=term_names,
                    )

                    idx_type = IndexType.BTREE
                    if hasattr(adapter, "parse_index_type"):
                        idx_type = adapter.parse_index_type(idx_type_raw)

                    canonical_indexes.append(
                        CanonicalIndex(
                            id=idx_id,
                            parent_table_id=tbl_id,
                            name=idx_name,
                            is_unique=is_unq,
                            is_primary=is_prim,
                            index_type=idx_type,
                            terms=sort_index_terms(terms),
                            predicate=predicate_val,
                            provenance=tbl_prov,
                        )
                    )

                # Process Triggers
                canonical_triggers: list[CanonicalTrigger] = []
                for tr_raw in triggers_by_table.get((s_name.lower(), t_name.lower()), []):
                    tr_name = _get_val(tr_raw, "trigger_name", "") or ""
                    timing_raw = str(
                        _get_val(tr_raw, "action_timing", _get_val(tr_raw, "timing", "BEFORE"))
                    ).upper()
                    event_raw = str(
                        _get_val(tr_raw, "event_manipulation", _get_val(tr_raw, "event", "INSERT"))
                    ).upper()
                    tr_defn = _get_val(
                        tr_raw, "action_statement", _get_val(tr_raw, "definition", None)
                    )

                    tr_id = compute_stable_object_id(
                        engine=self.engine,
                        object_kind=ObjectKind.TRIGGER,
                        native_name=tr_name,
                        namespace=s_name,
                        parent_id=tbl_id,
                        workspace_id=self.workspace_id,
                        connection_id=self.connection_id,
                    )

                    timing = (
                        TriggerTiming(timing_raw)
                        if timing_raw in TriggerTiming.__members__.values()
                        else TriggerTiming.BEFORE
                    )
                    event = (
                        TriggerEvent(event_raw)
                        if event_raw in TriggerEvent.__members__.values()
                        else TriggerEvent.INSERT
                    )

                    canonical_triggers.append(
                        CanonicalTrigger(
                            id=tr_id,
                            parent_table_id=tbl_id,
                            name=tr_name,
                            timing=timing,
                            event=event,
                            definition=tr_defn,
                            provenance=tbl_prov,
                        )
                    )

                canonical_tables.append(
                    CanonicalTable(
                        id=tbl_id,
                        namespace_id=ns_id,
                        name=t_name,
                        table_type=t_type,
                        columns=sorted_columns,
                        primary_key=canonical_pk,
                        foreign_keys=sort_foreign_keys(canonical_fk),
                        unique_constraints=sort_constraints(canonical_unique),
                        check_constraints=sort_constraints(canonical_check),
                        indexes=sort_indexes(canonical_indexes),
                        triggers=sort_triggers(canonical_triggers),
                        comment=t_comment,
                        provenance=tbl_prov,
                    )
                )

            # Build Views in Namespace
            canonical_views: list[CanonicalView] = []
            for v_raw in views_by_schema.get(s_name.lower(), []):
                v_name = _get_val(v_raw, "view_name") or _get_val(v_raw, "table_name", "") or ""
                v_defn = _get_val(v_raw, "view_definition", None)
                v_check = _get_val(v_raw, "check_option", None)
                v_updatable = bool(_get_val(v_raw, "is_updatable", False))

                v_id = compute_stable_object_id(
                    engine=self.engine,
                    object_kind=ObjectKind.VIEW,
                    native_name=v_name,
                    namespace=s_name,
                    parent_id=ns_id,
                    workspace_id=self.workspace_id,
                    connection_id=self.connection_id,
                )

                v_prov = MetadataProvenance(
                    source_engine=self.engine,
                    source_version=self.server_version,
                    connector_version=self.connector_version,
                    completeness=assess_engine_metadata_completeness(
                        self.engine, "views", self.capabilities
                    ),
                    native_identifier=v_name,
                    source_location=f"{s_name}.{v_name}",
                )

                canonical_views.append(
                    CanonicalView(
                        id=v_id,
                        namespace_id=ns_id,
                        name=v_name,
                        definition=v_defn,
                        check_option=v_check,
                        is_updatable=v_updatable,
                        provenance=v_prov,
                    )
                )

            canonical_namespaces.append(
                CanonicalNamespace(
                    id=ns_id,
                    name=s_name,
                    tables=sort_tables(canonical_tables),
                    views=sort_views(canonical_views),
                    provenance=ns_prov,
                )
            )

        # 5. Build Final CanonicalDatabase
        canonical_db = CanonicalDatabase(
            id=db_id,
            name=db_name,
            engine=self.engine,
            contract_version="1.0.0",
            namespaces=sort_namespaces(canonical_namespaces),
            provenance=db_provenance,
        )

        # 6. Validate References and Limits
        validate_canonical_database(canonical_db)

        return canonical_db
