"""DERA Canonical Metadata Normalization & Identity — Enums.

Defines strongly-typed enumerations for object kinds, canonical type taxonomy,
constraints, index methods, table classifications, and metadata completeness.
"""

from __future__ import annotations

from enum import StrEnum


class ObjectKind(StrEnum):
    """Enumeration of relational database object kinds."""

    DATABASE = "database"
    NAMESPACE = "namespace"
    TABLE = "table"
    COLUMN = "column"
    CONSTRAINT = "constraint"
    PRIMARY_KEY = "primary_key"
    FOREIGN_KEY = "foreign_key"
    UNIQUE_CONSTRAINT = "unique_constraint"
    CHECK_CONSTRAINT = "check_constraint"
    INDEX = "index"
    VIEW = "view"
    TRIGGER = "trigger"
    RELATIONSHIP = "relationship"


class CanonicalTypeCategory(StrEnum):
    """Engine-agnostic canonical classification taxonomy for database data types.

    Classifies diverse vendor-specific data types into a finite, deterministic set
    of semantic categories without erasing original native declarations.
    """

    INTEGER = "INTEGER"
    DECIMAL = "DECIMAL"
    FLOAT = "FLOAT"
    BOOLEAN = "BOOLEAN"
    TEXT = "TEXT"
    BINARY = "BINARY"
    DATE = "DATE"
    TIME = "TIME"
    TIMESTAMP = "TIMESTAMP"
    JSON = "JSON"
    UUID = "UUID"
    ENUM = "ENUM"
    SET = "SET"
    ARRAY = "ARRAY"
    SPATIAL = "SPATIAL"
    OTHER = "OTHER"
    UNKNOWN = "UNKNOWN"


class ConstraintType(StrEnum):
    """Types of relational database constraints."""

    PRIMARY_KEY = "PRIMARY_KEY"
    FOREIGN_KEY = "FOREIGN_KEY"
    UNIQUE = "UNIQUE"
    CHECK = "CHECK"


class ForeignKeyAction(StrEnum):
    """Referential integrity trigger actions for ON UPDATE and ON DELETE."""

    NO_ACTION = "NO ACTION"
    RESTRICT = "RESTRICT"
    CASCADE = "CASCADE"
    SET_NULL = "SET NULL"
    SET_DEFAULT = "SET DEFAULT"


class IndexType(StrEnum):
    """Storage and access method types for table indexes."""

    BTREE = "BTREE"
    HASH = "HASH"
    GIN = "GIN"
    GIST = "GIST"
    BRIN = "BRIN"
    SPGIST = "SPGIST"
    RTREE = "RTREE"
    FULLTEXT = "FULLTEXT"
    SPATIAL = "SPATIAL"
    OTHER = "OTHER"


class TableType(StrEnum):
    """Classification of relational table-like database entities."""

    TABLE = "TABLE"
    VIEW = "VIEW"
    MATERIALIZED_VIEW = "MATERIALIZED_VIEW"
    SYSTEM_TABLE = "SYSTEM_TABLE"
    FOREIGN_TABLE = "FOREIGN_TABLE"
    TEMPORARY_TABLE = "TEMPORARY_TABLE"
    PARTITIONED_TABLE = "PARTITIONED_TABLE"
    OTHER = "OTHER"


class TriggerTiming(StrEnum):
    """Execution timing for procedural triggers."""

    BEFORE = "BEFORE"
    AFTER = "AFTER"
    INSTEAD_OF = "INSTEAD OF"
    UNKNOWN = "UNKNOWN"


class TriggerEvent(StrEnum):
    """Mutation events that fire a database trigger."""

    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    TRUNCATE = "TRUNCATE"
    UNKNOWN = "UNKNOWN"


class GenerationMode(StrEnum):
    """Storage modes for computed or generated columns."""

    STORED = "STORED"
    VIRTUAL = "VIRTUAL"
    NONE = "NONE"


class MetadataCompleteness(StrEnum):
    """Confidence and completeness status of inspected metadata."""

    COMPLETE = "COMPLETE"
    PARTIAL = "PARTIAL"
    RESTRICTED = "RESTRICTED"
    UNSUPPORTED = "UNSUPPORTED"
    UNKNOWN = "UNKNOWN"


class IdentityScope(StrEnum):
    """Scoping level for canonical object identities."""

    SOURCE_LOCAL = "source_local"
    CONNECTION_SCOPED = "connection_scoped"
    WORKSPACE_SCOPED = "workspace_scoped"
