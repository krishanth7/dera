"""DERA Connectors — Universal Database Metadata Contracts.

Defines strongly-typed Pydantic v2 metadata models for schemas, tables, columns,
constraints, indexes, and views with deterministic sorting and identifier fidelity.
"""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class SchemaInfo(BaseModel):
    """Metadata representing a database schema or namespace."""

    model_config = ConfigDict(frozen=True)

    schema_name: str = Field(
        ...,
        description="Canonical schema or namespace identifier.",
    )
    comment: str | None = Field(
        default=None,
        description="Optional schema documentation or remark text.",
    )


class TableInfo(BaseModel):
    """Metadata representing a database table or relational object."""

    model_config = ConfigDict(frozen=True)

    schema_name: str = Field(
        ...,
        description="Schema name owning the table (or 'main'/'public').",
    )
    table_name: str = Field(
        ...,
        description="Canonical table identifier.",
    )
    object_type: str = Field(
        default="TABLE",
        description="Relational object type (e.g. TABLE, SYSTEM TABLE, PARTITIONED TABLE).",
    )
    comment: str | None = Field(
        default=None,
        description="Optional documentation or comment describing table purpose.",
    )
    engine_specific: dict[str, Any] = Field(
        default_factory=dict,
        description="Engine-specific non-standard attributes (e.g. table storage engine).",
    )

    @property
    def qualified_name(self) -> str:
        """Return the fully qualified 'schema.table' name."""
        return f"{self.schema_name}.{self.table_name}"


class ColumnInfo(BaseModel):
    """Metadata describing a single table column."""

    model_config = ConfigDict(frozen=True)

    schema_name: str = Field(
        ...,
        description="Schema name owning the parent table.",
    )
    table_name: str = Field(
        ...,
        description="Table name owning this column.",
    )
    column_name: str = Field(
        ...,
        description="Canonical column identifier.",
    )
    ordinal_position: int = Field(
        ...,
        description="1-based ordinal position of the column within the table definition.",
    )
    data_type: str = Field(
        ...,
        description="Engine-specific native data type definition (e.g. VARCHAR(255), INTEGER).",
    )
    is_nullable: bool = Field(
        default=True,
        description="True if column accepts NULL values, False if NOT NULL is enforced.",
    )
    default_expression: str | None = Field(
        default=None,
        description="Raw default expression text as stored in database metadata (untrusted string).",
    )
    is_identity: bool = Field(
        default=False,
        description="True if column is marked as auto-increment or generated identity.",
    )
    is_generated: bool = Field(
        default=False,
        description="True if column is a stored or virtual generated column.",
    )
    generation_expression: str | None = Field(
        default=None,
        description="Expression text for generated columns.",
    )
    comment: str | None = Field(
        default=None,
        description="Optional documentation or remark for this column.",
    )
    engine_specific: dict[str, Any] = Field(
        default_factory=dict,
        description="Engine-specific column properties (e.g. collation, unsigned, precision, scale).",
    )


class PrimaryKeyInfo(BaseModel):
    """Metadata representing a primary key constraint."""

    model_config = ConfigDict(frozen=True)

    constraint_name: str | None = Field(
        default=None,
        description="Constraint identifier if named by database engine.",
    )
    schema_name: str = Field(
        ...,
        description="Schema name owning the table.",
    )
    table_name: str = Field(
        ...,
        description="Table name owning this primary key.",
    )
    column_names: list[str] = Field(
        ...,
        description="Ordered list of column names comprising the primary key.",
    )


class ForeignKeyInfo(BaseModel):
    """Metadata representing a foreign key relationship."""

    model_config = ConfigDict(frozen=True)

    constraint_name: str | None = Field(
        default=None,
        description="Foreign key constraint identifier.",
    )
    schema_name: str = Field(
        ...,
        description="Schema name owning the referencing table.",
    )
    table_name: str = Field(
        ...,
        description="Referencing table name.",
    )
    column_names: list[str] = Field(
        ...,
        description="Ordered list of foreign key column names on the source table.",
    )
    referenced_schema: str = Field(
        ...,
        description="Schema name of the referenced target table.",
    )
    referenced_table: str = Field(
        ...,
        description="Target table name referenced by this foreign key.",
    )
    referenced_columns: list[str] = Field(
        ...,
        description="Ordered list of referenced column names on the target table.",
    )
    on_update: str = Field(
        default="NO ACTION",
        description="Referential action triggered on update (e.g. CASCADE, SET NULL, RESTRICT).",
    )
    on_delete: str = Field(
        default="NO ACTION",
        description="Referential action triggered on delete (e.g. CASCADE, SET NULL, RESTRICT).",
    )


class UniqueConstraintInfo(BaseModel):
    """Metadata representing a unique key or unique constraint."""

    model_config = ConfigDict(frozen=True)

    constraint_name: str | None = Field(
        default=None,
        description="Unique constraint name if assigned by database engine.",
    )
    schema_name: str = Field(
        ...,
        description="Schema name owning the table.",
    )
    table_name: str = Field(
        ...,
        description="Table name owning this unique constraint.",
    )
    column_names: list[str] = Field(
        ...,
        description="Ordered list of column names forming the unique constraint.",
    )


class CheckConstraintInfo(BaseModel):
    """Metadata representing a check constraint."""

    model_config = ConfigDict(frozen=True)

    constraint_name: str | None = Field(
        default=None,
        description="Check constraint name if available.",
    )
    schema_name: str = Field(
        ...,
        description="Schema name owning the table.",
    )
    table_name: str = Field(
        ...,
        description="Table name owning this check constraint.",
    )
    check_clause: str = Field(
        ...,
        description="Check condition expression text as stored in database catalog (untrusted string).",
    )


class IndexInfo(BaseModel):
    """Metadata describing a secondary database index."""

    model_config = ConfigDict(frozen=True)

    index_name: str = Field(
        ...,
        description="Canonical index identifier.",
    )
    schema_name: str = Field(
        ...,
        description="Schema name owning the indexed table.",
    )
    table_name: str = Field(
        ...,
        description="Table name on which the index is built.",
    )
    column_names: list[str] = Field(
        ...,
        description="Ordered list of indexed column names or expressions.",
    )
    is_unique: bool = Field(
        default=False,
        description="True if index enforces unique values.",
    )
    is_primary: bool = Field(
        default=False,
        description="True if this index backs a primary key constraint.",
    )
    index_type: str | None = Field(
        default=None,
        description="Index access method (e.g. BTREE, HASH, GIN, GIST, BRIN).",
    )
    predicate: str | None = Field(
        default=None,
        description="Predicate filter clause for partial or filtered indexes.",
    )
    engine_specific: dict[str, Any] = Field(
        default_factory=dict,
        description="Engine-specific index options (e.g. collation, nulls ordering).",
    )


class ViewInfo(BaseModel):
    """Metadata describing a database view or materialized view."""

    model_config = ConfigDict(frozen=True)

    schema_name: str = Field(
        ...,
        description="Schema name owning the view.",
    )
    view_name: str = Field(
        ...,
        description="Canonical view identifier.",
    )
    is_materialized: bool = Field(
        default=False,
        description="True if the view is a materialized view with stored data.",
    )
    view_definition: str | None = Field(
        default=None,
        description="SQL definition statement for the view (metadata text only; never executed).",
    )
    comment: str | None = Field(
        default=None,
        description="Optional documentation or remark for the view.",
    )
    engine_specific: dict[str, Any] = Field(
        default_factory=dict,
        description="Engine-specific view properties (e.g. security options, check options).",
    )
