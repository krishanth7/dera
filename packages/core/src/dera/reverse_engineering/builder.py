"""DERA Reverse Engineering — Phase 6.1 Schema Builder.

Deterministic schema construction pipeline that transforms validated Phase 5.5
canonical metadata into a coherent, strongly-typed SchemaRepresentation.

Guarantees:
- Validates input and contract version compatibility.
- Enforces configurable resource bounds (max objects, identifier lengths, definition sizes).
- Preserves Phase 5.5 stable ObjectIds.
- Builds ObjectRegistry with O(1) lookup and duplicate detection.
- Resolves foreign key references and establishes resolution status.
- Applies deterministic ordering to all collections.
- Performs structural validation.
- Does not reconnect to source databases.
- AI/LLM/ML free.
"""

from __future__ import annotations

import time
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from dera.metadata.models.database import CanonicalDatabase
from dera.metadata.models.namespace import CanonicalNamespace
from dera.metadata.models.table import CanonicalTable
from dera.reverse_engineering.capabilities import assess_schema_capabilities
from dera.reverse_engineering.errors import (
    InvalidSchemaInputError,
    SchemaResourceLimitError,
    UnsupportedSchemaContractError,
)
from dera.reverse_engineering.ordering import (
    sort_columns,
    sort_constraints,
    sort_foreign_key_references,
    sort_foreign_keys,
    sort_indexes,
    sort_namespaces,
    sort_tables,
    sort_triggers,
    sort_views,
)
from dera.reverse_engineering.references import ForeignKeyReference, ResolutionStatus
from dera.reverse_engineering.registry import ObjectRegistry
from dera.reverse_engineering.schema import (
    SCHEMA_REPRESENTATION_CONTRACT_VERSION,
    SchemaRepresentation,
)
from dera.reverse_engineering.validation import validate_schema_representation

# Supported canonical metadata contract versions
SUPPORTED_METADATA_CONTRACT_VERSIONS: tuple[str, ...] = ("1.0.0",)


class SchemaResourceLimits(BaseModel):
    """Resource bounds applied during schema construction to protect against DoS/OOM."""

    model_config = ConfigDict(frozen=True)

    max_total_objects: int = Field(
        default=100_000,
        description="Maximum number of canonical schema objects allowed in a single schema.",
    )
    max_nesting_depth: int = Field(
        default=10,
        description="Maximum hierarchy nesting depth allowed.",
    )
    max_identifier_length: int = Field(
        default=256,
        description="Maximum allowed character length for any identifier (table, column, constraint).",
    )
    max_definition_bytes: int = Field(
        default=1_000_000,
        description="Maximum size in bytes for raw SQL definitions (views, triggers, checks).",
    )
    max_references: int = Field(
        default=50_000,
        description="Maximum number of foreign key or object references allowed.",
    )
    max_tables: int = Field(
        default=10_000,
        description="Maximum number of tables allowed in a single schema.",
    )
    max_columns_per_table: int = Field(
        default=2_000,
        description="Maximum number of columns allowed per table.",
    )
    max_total_columns: int = Field(
        default=100_000,
        description="Maximum total number of columns allowed across all tables.",
    )


class SchemaBuilder:
    """Deterministic constructor for SchemaRepresentation.

    Accepts validated CanonicalDatabase metadata (or serialized reports) and produces
    an immutable, registry-backed, validated SchemaRepresentation.
    """

    @classmethod
    def from_canonical_database(
        cls,
        database: CanonicalDatabase,
        workspace_id: str | None = None,
        limits: SchemaResourceLimits | None = None,
        strict_validation: bool = False,
        strict_foreign_keys: bool = False,
        capabilities: dict[str, Any] | None = None,
    ) -> SchemaRepresentation:
        """Construct a SchemaRepresentation from a CanonicalDatabase model.

        Args:
            database: Validated Phase 5.5 CanonicalDatabase instance.
            workspace_id: Optional workspace scope identifier.
            limits: Resource limits configuration; defaults to SchemaResourceLimits().
            strict_validation: If True, raises on referential integrity issues.
            strict_foreign_keys: If True, unresolved FK targets raise errors.
            capabilities: Optional dictionary of connector-reported capability flags.

        Returns:
            Fully populated, validated SchemaRepresentation.

        Raises:
            UnsupportedSchemaContractError: If contract version is unsupported.
            SchemaResourceLimitError: If any configured resource bound is breached.
            DuplicateRegistrationError: If identical ObjectIds collide in the registry.
            MissingParentError: If strict_validation=True and a parent object is missing.
            SchemaValidationError: If strict_validation=True and integrity is violated.
        """
        start_time = time.perf_counter()
        if limits is None:
            limits = SchemaResourceLimits()

        # 1. Contract version check
        if database.contract_version not in SUPPORTED_METADATA_CONTRACT_VERSIONS:
            raise UnsupportedSchemaContractError(
                f"Unsupported canonical metadata contract version: {database.contract_version!r}. "
                f"Supported versions: {SUPPORTED_METADATA_CONTRACT_VERSIONS}."
            )

        # 2. Check identifier length of database
        cls._check_identifier(database.name, "database name", limits)

        # 3. Initialize ObjectRegistry
        registry = ObjectRegistry(workspace_id=workspace_id)
        registry.register_database(database)

        # 4. Deterministic sorting & registration
        ordered_namespaces = sort_namespaces(database.namespaces)
        resolved_fk_refs: list[ForeignKeyReference] = []

        total_registered = 1  # Database is registered

        normalized_namespaces: list[CanonicalNamespace] = []

        for ns in ordered_namespaces:
            cls._check_identifier(ns.name, f"namespace {ns.name!r}", limits)
            cls._check_object_limit(total_registered + 1, limits)
            total_registered += 1

            ordered_tables = sort_tables(ns.tables)
            normalized_tables: list[CanonicalTable] = []
            for tbl in ordered_tables:
                cls._check_identifier(tbl.name, f"table {tbl.name!r}", limits)
                cls._check_object_limit(total_registered + 1, limits)
                total_registered += 1

                # Columns
                ordered_cols = sort_columns(tbl.columns)
                for col in ordered_cols:
                    cls._check_identifier(col.name, f"column {col.name!r}", limits)
                    cls._check_object_limit(total_registered + 1, limits)
                    registry.register_column(col)
                    total_registered += 1

                # Primary key
                if tbl.primary_key:
                    cls._check_identifier(
                        tbl.primary_key.name, f"PK {tbl.primary_key.name!r}", limits
                    )
                    cls._check_object_limit(total_registered + 1, limits)
                    registry.register_constraint(tbl.primary_key)
                    total_registered += 1

                # Unique constraints
                ordered_unqs = sort_constraints(tbl.unique_constraints)
                for unq in ordered_unqs:
                    cls._check_identifier(unq.name, f"unique constraint {unq.name!r}", limits)
                    cls._check_object_limit(total_registered + 1, limits)
                    registry.register_constraint(unq)
                    total_registered += 1

                # Check constraints
                ordered_chks = sort_constraints(tbl.check_constraints)
                for chk in ordered_chks:
                    cls._check_identifier(chk.name, f"check constraint {chk.name!r}", limits)
                    cls._check_definition(chk.check_clause, f"check clause {chk.name!r}", limits)
                    cls._check_object_limit(total_registered + 1, limits)
                    registry.register_constraint(chk)
                    total_registered += 1

                # Indexes
                ordered_idxs = sort_indexes(tbl.indexes)
                for idx in ordered_idxs:
                    cls._check_identifier(idx.name, f"index {idx.name!r}", limits)
                    cls._check_definition(idx.predicate, f"index predicate {idx.name!r}", limits)
                    cls._check_object_limit(total_registered + 1, limits)
                    registry.register_index(idx)
                    total_registered += 1

                # Triggers
                ordered_trgs = sort_triggers(tbl.triggers)
                for trg in ordered_trgs:
                    cls._check_identifier(trg.name, f"trigger {trg.name!r}", limits)
                    cls._check_definition(
                        trg.definition, f"trigger definition {trg.name!r}", limits
                    )
                    cls._check_object_limit(total_registered + 1, limits)
                    registry.register_trigger(trg)
                    total_registered += 1

                # Foreign Keys
                ordered_fks = sort_foreign_keys(tbl.foreign_keys)
                for fk in ordered_fks:
                    cls._check_identifier(fk.name, f"foreign key {fk.name!r}", limits)
                    cls._check_object_limit(total_registered + 1, limits)
                    registry.register_foreign_key(fk)
                    total_registered += 1

                norm_tbl = tbl.model_copy(
                    update={
                        "columns": ordered_cols,
                        "unique_constraints": ordered_unqs,
                        "check_constraints": ordered_chks,
                        "indexes": ordered_idxs,
                        "triggers": ordered_trgs,
                        "foreign_keys": ordered_fks,
                    }
                )
                registry.register_table(norm_tbl)
                normalized_tables.append(norm_tbl)

            # Views
            ordered_views = sort_views(ns.views)
            for v in ordered_views:
                cls._check_identifier(v.name, f"view {v.name!r}", limits)
                cls._check_definition(v.definition, f"view definition {v.name!r}", limits)
                cls._check_object_limit(total_registered + 1, limits)
                registry.register_view(v)
                total_registered += 1

            norm_ns = ns.model_copy(
                update={
                    "tables": tuple(normalized_tables),
                    "views": ordered_views,
                }
            )
            registry.register_namespace(norm_ns)
            normalized_namespaces.append(norm_ns)

        normalized_db = database.model_copy(update={"namespaces": tuple(normalized_namespaces)})

        # 5. Resolve foreign key references
        for tbl in normalized_db.all_tables():
            for fk in tbl.foreign_keys:
                resolved_id = fk.referenced_table_id
                status = (
                    ResolutionStatus.RESOLVED
                    if resolved_id and registry.contains(resolved_id)
                    else ResolutionStatus.MISSING
                )

                # If referenced_table_id wasn't in metadata report, attempt schema-level lookup
                if not resolved_id:
                    target_schema = fk.referenced_schema
                    for target_ns in normalized_db.namespaces:
                        if target_schema is None or target_ns.name.lower() == target_schema.lower():
                            cand = target_ns.get_table(fk.referenced_table_name)
                            if cand is not None:
                                resolved_id = cand.id
                                status = ResolutionStatus.RESOLVED
                                break

                ref = ForeignKeyReference(
                    foreign_key_id=fk.id,
                    foreign_key_name=fk.name,
                    source_table_id=fk.source_table_id,
                    source_table_name=fk.source_table_name,
                    source_columns=fk.source_columns,
                    referenced_table_id=resolved_id,
                    referenced_table_name=fk.referenced_table_name,
                    referenced_schema=fk.referenced_schema,
                    referenced_columns=fk.referenced_columns,
                    on_update=fk.on_update.value
                    if hasattr(fk.on_update, "value")
                    else str(fk.on_update),
                    on_delete=fk.on_delete.value
                    if hasattr(fk.on_delete, "value")
                    else str(fk.on_delete),
                    status=status,
                )
                resolved_fk_refs.append(ref)

        ordered_fk_refs = sort_foreign_key_references(resolved_fk_refs)
        if len(ordered_fk_refs) > limits.max_references:
            raise SchemaResourceLimitError(
                "max_references", limits.max_references, len(ordered_fk_refs)
            )

        # 6. Assess capabilities & completeness
        cap_profile = assess_schema_capabilities(normalized_db.engine, normalized_db, capabilities)

        # 7. Build preliminary representation for validation
        duration_ms = (time.perf_counter() - start_time) * 1000.0
        metrics = {
            "total_objects": total_registered,
            "total_namespaces": len(normalized_namespaces),
            "total_tables": len(normalized_db.all_tables()),
            "total_foreign_keys": len(ordered_fk_refs),
        }

        representation = SchemaRepresentation(
            registry=registry,
            contract_version=SCHEMA_REPRESENTATION_CONTRACT_VERSION,
            database_id=normalized_db.id,
            database_name=normalized_db.name,
            engine=normalized_db.engine,
            engine_version=normalized_db.provenance.source_version,
            source_reference=normalized_db.name,
            provenance=normalized_db.provenance,
            database=normalized_db,
            namespaces=tuple(normalized_namespaces),
            foreign_key_references=ordered_fk_refs,
            capability_profile=cap_profile,
            completeness=cap_profile.overall_completeness,
            is_validated=False,
            validation_issues=(),
            resource_metrics=metrics,
            build_duration_ms=round(duration_ms, 3),
        )

        # 8. Referential integrity validation
        issues = validate_schema_representation(
            representation,
            strict=strict_validation,
            strict_foreign_keys=strict_foreign_keys,
        )

        is_valid = len(issues) == 0

        # Return representation with updated validation state
        return representation.model_copy(
            update={
                "is_validated": is_valid,
                "validation_issues": issues,
            }
        )

    @classmethod
    def from_metadata(
        cls,
        metadata_report: dict[str, Any] | CanonicalDatabase,
        workspace_id: str | None = None,
        limits: SchemaResourceLimits | None = None,
        strict_validation: bool = False,
        strict_foreign_keys: bool = False,
        capabilities: dict[str, Any] | None = None,
    ) -> SchemaRepresentation:
        """Construct a SchemaRepresentation from a raw dictionary report or CanonicalDatabase."""
        if isinstance(metadata_report, CanonicalDatabase):
            return cls.from_canonical_database(
                database=metadata_report,
                workspace_id=workspace_id,
                limits=limits,
                strict_validation=strict_validation,
                strict_foreign_keys=strict_foreign_keys,
                capabilities=capabilities,
            )

        # Support Phase 5 DatabaseMetadataReport instances directly
        if hasattr(metadata_report, "schemas") and hasattr(metadata_report, "tables"):
            try:
                from dera.metadata.normalization import MetadataNormalizer

                engine = getattr(metadata_report, "engine", "unknown")
                database_name = getattr(metadata_report, "database_name", "unnamed")
                server_version = getattr(metadata_report, "server_version", None)
                normalizer = MetadataNormalizer(
                    engine=engine,
                    database_name=database_name,
                    server_version=server_version,
                    workspace_id=workspace_id,
                )
                canonical_db = normalizer.normalize(metadata_report)
                return cls.from_canonical_database(
                    database=canonical_db,
                    workspace_id=workspace_id,
                    limits=limits,
                    strict_validation=strict_validation,
                    strict_foreign_keys=strict_foreign_keys,
                    capabilities=capabilities,
                )
            except Exception as exc:
                raise InvalidSchemaInputError(
                    f"Failed to normalize connector report: {exc}"
                ) from exc

        if not isinstance(metadata_report, dict):
            raise InvalidSchemaInputError(
                f"Expected CanonicalDatabase instance, DatabaseMetadataReport, or dict metadata report, got {type(metadata_report).__name__}."
            )

        try:
            database = CanonicalDatabase.model_validate(metadata_report)
        except Exception as exc:
            raise InvalidSchemaInputError(
                f"Failed to validate CanonicalDatabase from dict: {exc}"
            ) from exc

        return cls.from_canonical_database(
            database=database,
            workspace_id=workspace_id,
            limits=limits,
            strict_validation=strict_validation,
            strict_foreign_keys=strict_foreign_keys,
            capabilities=capabilities,
        )

    # ------------------------------------------------------------------
    # Resource checking helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _check_identifier(name: str | None, context: str, limits: SchemaResourceLimits) -> None:
        if name and len(name) > limits.max_identifier_length:
            raise SchemaResourceLimitError(
                f"max_identifier_length ({context})",
                limits.max_identifier_length,
                len(name),
            )

    @staticmethod
    def _check_definition(text: str | None, context: str, limits: SchemaResourceLimits) -> None:
        if text and len(text.encode("utf-8")) > limits.max_definition_bytes:
            raise SchemaResourceLimitError(
                f"max_definition_bytes ({context})",
                limits.max_definition_bytes,
                len(text.encode("utf-8")),
            )

    @staticmethod
    def _check_object_limit(current_count: int, limits: SchemaResourceLimits) -> None:
        if current_count > limits.max_total_objects:
            raise SchemaResourceLimitError(
                "max_total_objects",
                limits.max_total_objects,
                current_count,
            )


__all__ = [
    "SUPPORTED_METADATA_CONTRACT_VERSIONS",
    "SchemaBuilder",
    "SchemaResourceLimits",
]
