"""Structural reconstruction builder pipeline for Phase 6.2.

Provides the orchestration pipeline converting SchemaRepresentation or CanonicalDatabase
into a validated, strongly typed StructuralReconstructionResult with deterministic hashing.
"""

import hashlib
import json
import time
from typing import Any

from dera.metadata.models import CanonicalDatabase
from dera.reverse_engineering.builder import SchemaBuilder, SchemaResourceLimits
from dera.reverse_engineering.errors import SchemaResourceLimitError, UnsupportedSchemaContractError
from dera.reverse_engineering.reconstruction.models import (
    ReconstructedTable,
    ReconstructionMode,
    StructuralReconstructionResult,
)
from dera.reverse_engineering.reconstruction.ordering import sort_tables
from dera.reverse_engineering.reconstruction.references import resolve_all_references
from dera.reverse_engineering.reconstruction.tables import reconstruct_table
from dera.reverse_engineering.reconstruction.validation import validate_structural_reconstruction
from dera.reverse_engineering.schema import SchemaRepresentation


def compute_structural_hash(
    tables: tuple[ReconstructedTable, ...], database_name: str, engine: str
) -> str:
    """Compute a deterministic SHA-256 hash across reconstructed tables."""
    payload = {
        "contract_version": "1.0.0",
        "database_name": database_name,
        "engine": engine,
        "tables": [t.model_dump(mode="json") for t in tables],
    }
    canonical_json = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


class StructuralReconstructionBuilder:
    """Builder pipeline constructing validated StructuralReconstructionResult instances."""

    def __init__(
        self,
        mode: ReconstructionMode = ReconstructionMode.STRICT,
        limits: SchemaResourceLimits | None = None,
    ) -> None:
        self.mode = mode
        self.limits = limits or SchemaResourceLimits()

    def build_from_schema(
        self,
        schema: SchemaRepresentation,
    ) -> StructuralReconstructionResult:
        """Reconstruct schema structure from a Phase 6.1 SchemaRepresentation."""
        start_time = time.perf_counter()

        if schema.contract_version != "1.0.0":
            raise UnsupportedSchemaContractError(
                f"Unsupported contract version '{schema.contract_version}'. Expected '1.0.0'."
            )

        # 1. Enforce Resource Limits
        schema_tables = (
            schema.all_tables() if hasattr(schema, "all_tables") else getattr(schema, "tables", ())
        )
        total_tables = len(schema_tables)
        if total_tables > self.limits.max_tables:
            raise SchemaResourceLimitError(
                "max_tables",
                self.limits.max_tables,
                total_tables,
            )

        total_cols = sum(len(t.columns) for t in schema_tables)
        if total_cols > self.limits.max_total_columns:
            raise SchemaResourceLimitError(
                "max_total_columns",
                self.limits.max_total_columns,
                total_cols,
            )

        # 2. Reconstruct Tables
        reconstructed_list: list[ReconstructedTable] = []
        for t in schema_tables:
            if len(t.columns) > self.limits.max_columns_per_table:
                raise SchemaResourceLimitError(
                    "max_columns_per_table",
                    self.limits.max_columns_per_table,
                    len(t.columns),
                )
            reconstructed_list.append(reconstruct_table(t, schema.engine, schema.registry))

        # 3. Resolve References against Registry
        resolved_tables = resolve_all_references(reconstructed_list, schema.registry)

        # 4. Deterministic Multi-Key Sorting
        ordered_tables = sort_tables(resolved_tables)

        # 5. Structural Validation
        findings = validate_structural_reconstruction(ordered_tables, mode=self.mode)

        # 6. Deterministic Hashing
        schema_hash = compute_structural_hash(ordered_tables, schema.database_name, schema.engine)

        duration_ms = round((time.perf_counter() - start_time) * 1000.0, 3)

        resource_metrics: dict[str, Any] = {
            "total_tables": len(ordered_tables),
            "total_columns": sum(len(t.columns) for t in ordered_tables),
            "total_foreign_keys": sum(len(t.foreign_keys) for t in ordered_tables),
            "total_unique_constraints": sum(len(t.unique_constraints) for t in ordered_tables),
            "total_check_constraints": sum(len(t.check_constraints) for t in ordered_tables),
            "reconstruction_duration_ms": duration_ms,
        }

        return StructuralReconstructionResult(
            contract_version="1.0.0",
            schema_hash=schema_hash,
            database_name=schema.database_name,
            engine=schema.engine,
            reconstruction_mode=self.mode,
            tables=ordered_tables,
            findings=findings,
            capability_profile=schema.capability_profile,
            resource_metrics=resource_metrics,
            provenance=schema.provenance,
        )

    def build_from_canonical(
        self,
        canonical_db: CanonicalDatabase,
    ) -> StructuralReconstructionResult:
        """Reconstruct directly from a Phase 5.5 CanonicalDatabase."""
        schema = SchemaBuilder.from_canonical_database(canonical_db, limits=self.limits)
        return self.build_from_schema(schema)

    def build(
        self,
        schema_input: SchemaRepresentation | CanonicalDatabase,
    ) -> StructuralReconstructionResult:
        """Unified entrypoint supporting SchemaRepresentation and CanonicalDatabase."""
        if isinstance(schema_input, SchemaRepresentation):
            return self.build_from_schema(schema_input)
        if isinstance(schema_input, CanonicalDatabase):
            return self.build_from_canonical(schema_input)
        raise UnsupportedSchemaContractError(
            f"Unsupported input type '{type(schema_input).__name__}'. Expected SchemaRepresentation or CanonicalDatabase."
        )
