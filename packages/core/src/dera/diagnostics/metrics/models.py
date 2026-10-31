"""DERA Diagnostics — Maintainability Metrics Data Models.

Defines typed Pydantic models for maintainability metric definitions,
metric observations, schema complexity aggregates, table width attributes,
and namespace distributions.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class MaintainabilityMetricScope(StrEnum):
    """Categorical hierarchy level of a maintainability metric."""

    DATABASE = "DATABASE"
    SCHEMA = "SCHEMA"
    TABLE = "TABLE"
    COLUMN = "COLUMN"
    RELATIONSHIP = "RELATIONSHIP"


class MaintainabilityMetricDefinition(BaseModel):
    """Formal specification of an explainable maintainability metric."""

    model_config = ConfigDict(frozen=True)

    metric_id: str = Field(description="Deterministic stable metric identifier.")
    name: str = Field(description="Human-readable title of the metric.")
    definition: str = Field(description="Concise description of what the metric measures.")
    formula: str = Field(description="Mathematical or algorithmic formula used for computation.")
    unit: str = Field(description="Measurement unit (e.g. 'count', 'ratio', 'levels').")
    scope: MaintainabilityMetricScope = Field(description="Target structural hierarchy level.")
    applicability: str = Field(description="Supported database engines and required metadata.")
    limitations: str = Field(
        description="Known boundaries, non-goals, and interpretation constraints."
    )
    version: str = Field(default="1.0.0", description="Semantic version of the metric definition.")


class SchemaComplexityMetrics(BaseModel):
    """Aggregated structural complexity metrics for an inspected database schema."""

    model_config = ConfigDict(frozen=True)

    table_count: int = Field(ge=0, description="Total number of relational tables.")
    view_count: int = Field(ge=0, description="Total number of database views.")
    column_count: int = Field(ge=0, description="Total number of table columns.")
    constraint_count: int = Field(
        ge=0, description="Total count of primary, foreign, unique, and check constraints."
    )
    index_count: int = Field(ge=0, description="Total number of secondary indexes.")
    foreign_key_count: int = Field(ge=0, description="Total number of foreign key relationships.")
    namespace_count: int = Field(
        ge=0, description="Total number of database schemas or namespaces."
    )
    avg_columns_per_table: float = Field(ge=0.0, description="Average number of columns per table.")
    avg_constraints_per_table: float = Field(
        ge=0.0, description="Average number of constraints per table."
    )


class TableMaintainabilityMetrics(BaseModel):
    """Structural maintainability metrics for an individual table."""

    model_config = ConfigDict(frozen=True)

    object_id: str = Field(description="Canonical ObjectId of the table.")
    table_name: str = Field(description="Native name of the table.")
    namespace: str = Field(description="Owning schema/namespace name.")
    column_count: int = Field(ge=0, description="Total number of columns declared on this table.")
    nullable_column_count: int = Field(ge=0, description="Number of columns that permit NULL.")
    nullability_ratio: float = Field(
        ge=0.0, le=1.0, description="Ratio of nullable columns to total columns."
    )
    default_expression_count: int = Field(
        ge=0, description="Number of columns with default value expressions."
    )
    identity_column_count: int = Field(
        ge=0, description="Number of auto-increment or identity columns."
    )
    generated_column_count: int = Field(
        ge=0, description="Number of virtual or stored generated columns."
    )
    lob_column_count: int = Field(
        ge=0, description="Number of large text (TEXT, CLOB) or binary (BLOB) columns."
    )


class NamespaceMaintainabilityMetrics(BaseModel):
    """Distribution metrics for an individual namespace or schema."""

    model_config = ConfigDict(frozen=True)

    namespace_name: str = Field(description="Native schema/namespace identifier.")
    table_count: int = Field(ge=0, description="Number of tables residing in this namespace.")
    view_count: int = Field(ge=0, description="Number of views residing in this namespace.")
    total_objects: int = Field(ge=0, description="Total tables and views in this namespace.")
    object_share_ratio: float = Field(
        ge=0.0, le=1.0, description="Proportion of database tables in this namespace."
    )


class NamingComplianceMetrics(BaseModel):
    """Compliance metrics evaluating identifiers against a configured naming profile."""

    model_config = ConfigDict(frozen=True)

    profile_name: str = Field(
        description="Evaluated naming convention (e.g. 'snake_case', 'camelCase')."
    )
    total_evaluated: int = Field(ge=0, description="Total identifier names evaluated.")
    compliant_count: int = Field(ge=0, description="Identifiers adhering to the naming profile.")
    non_compliant_count: int = Field(
        ge=0, description="Identifiers deviating from the naming profile."
    )
    compliance_ratio: float = Field(
        ge=0.0, le=1.0, description="Ratio of compliant identifiers to total evaluated."
    )


class CouplingMaintainabilityMetrics(BaseModel):
    """Relational coupling and dependency metrics for an individual table node."""

    model_config = ConfigDict(frozen=True)

    node_id: str = Field(description="Canonical ObjectId of the table node.")
    table_name: str = Field(description="Fully qualified table name (namespace.table).")
    in_degree: int = Field(
        ge=0, description="Direct prerequisite parent dependencies (outgoing edges)."
    )
    out_degree: int = Field(
        ge=0, description="Direct downstream child dependents (incoming edges)."
    )
    total_degree: int = Field(
        ge=0, description="Combined relational degree (in_degree + out_degree)."
    )
    is_in_cycle: bool = Field(
        description="True if node belongs to a cyclic Strongly Connected Component."
    )
    condensation_depth: int = Field(ge=0, description="Depth level in the Condensation DAG.")
    transitive_dependents_count: int = Field(
        ge=0, description="Total downstream transitive dependents (blast radius)."
    )


class MaintainabilityMetricsReport(BaseModel):
    """Root container encapsulating complete schema maintainability metrics."""

    model_config = ConfigDict(frozen=True)

    contract_version: str = Field(default="1.0.0", description="Contract specification version.")
    database_name: str = Field(description="Logical database identifier.")
    engine: str = Field(description="Database engine type.")
    schema_complexity: SchemaComplexityMetrics = Field(
        description="Aggregated schema complexity metrics."
    )
    table_metrics: tuple[TableMaintainabilityMetrics, ...] = Field(
        default_factory=tuple,
        description="Individual table maintainability metrics sorted by table name.",
    )
    namespace_metrics: tuple[NamespaceMaintainabilityMetrics, ...] = Field(
        default_factory=tuple,
        description="Per-namespace distribution metrics sorted by namespace name.",
    )
    naming_compliance: NamingComplianceMetrics = Field(
        description="Identifier naming compliance metrics."
    )
    coupling_metrics: tuple[CouplingMaintainabilityMetrics, ...] = Field(
        default_factory=tuple,
        description="Per-node coupling and dependency metrics sorted by table name.",
    )
    metadata_context: dict[str, Any] = Field(
        default_factory=dict,
        description="Execution context data (timestamps, thresholds, and limits).",
    )
