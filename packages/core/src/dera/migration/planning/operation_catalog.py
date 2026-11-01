"""Operation Catalog for Phase 9.3 Migration Planning.

Defines supported abstract operations, required preconditions, postconditions,
engine capabilities across PostgreSQL, Supabase, SQLite, MySQL, and MariaDB,
and deterministic validation templates.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from dera.migration.planning.enums import (
    EngineCapabilityState,
    MigrationOperationType,
    PreconditionType,
)


class CatalogEntry(BaseModel):
    """Catalog specification for a supported migration operation type."""
    operation_type: MigrationOperationType
    description: str
    default_preconditions: List[PreconditionType] = Field(default_factory=list)
    engine_capabilities: Dict[str, EngineCapabilityState] = Field(default_factory=dict)
    engine_limitations: Dict[str, List[str]] = Field(default_factory=dict)
    requires_manual_gate_if_destructive: bool = True
    requires_data_validation: bool = False


class OperationCatalog:
    """Versioned deterministic operation catalog."""
    CATALOG_VERSION = "1.0.0"

    _ENTRIES: Dict[MigrationOperationType, CatalogEntry] = {
        MigrationOperationType.CREATE_NAMESPACE: CatalogEntry(
            operation_type=MigrationOperationType.CREATE_NAMESPACE,
            description="Create database schema/namespace.",
            default_preconditions=[PreconditionType.OBJECT_ABSENCE, PreconditionType.PERMISSION_VERIFICATION],
            engine_capabilities={
                "postgresql": EngineCapabilityState.SUPPORTED,
                "supabase": EngineCapabilityState.SUPPORTED,
                "sqlite": EngineCapabilityState.UNSUPPORTED,  # SQLite has single schema/attached DBs
                "mysql": EngineCapabilityState.SUPPORTED,     # SCHEMA/DATABASE
                "mariadb": EngineCapabilityState.SUPPORTED,
            },
            engine_limitations={
                "sqlite": ["SQLite does not have native multiple namespace/schema support within a single file."]
            }
        ),
        MigrationOperationType.DROP_NAMESPACE: CatalogEntry(
            operation_type=MigrationOperationType.DROP_NAMESPACE,
            description="Drop database schema/namespace.",
            default_preconditions=[PreconditionType.OBJECT_EXISTENCE, PreconditionType.BACKUP_PRESERVATION_REVIEW],
            engine_capabilities={
                "postgresql": EngineCapabilityState.SUPPORTED,
                "supabase": EngineCapabilityState.SUPPORTED,
                "sqlite": EngineCapabilityState.UNSUPPORTED,
                "mysql": EngineCapabilityState.SUPPORTED,
                "mariadb": EngineCapabilityState.SUPPORTED,
            },
            engine_limitations={
                "sqlite": ["SQLite does not have native namespace drops."]
            }
        ),
        MigrationOperationType.CREATE_TABLE: CatalogEntry(
            operation_type=MigrationOperationType.CREATE_TABLE,
            description="Create table structure.",
            default_preconditions=[PreconditionType.OBJECT_ABSENCE, PreconditionType.DEPENDENCY_RESOLUTION],
            engine_capabilities={
                "postgresql": EngineCapabilityState.SUPPORTED,
                "supabase": EngineCapabilityState.SUPPORTED,
                "sqlite": EngineCapabilityState.SUPPORTED,
                "mysql": EngineCapabilityState.SUPPORTED,
                "mariadb": EngineCapabilityState.SUPPORTED,
            }
        ),
        MigrationOperationType.DROP_TABLE: CatalogEntry(
            operation_type=MigrationOperationType.DROP_TABLE,
            description="Drop table structure and data.",
            default_preconditions=[PreconditionType.OBJECT_EXISTENCE, PreconditionType.BACKUP_PRESERVATION_REVIEW],
            engine_capabilities={
                "postgresql": EngineCapabilityState.SUPPORTED,
                "supabase": EngineCapabilityState.SUPPORTED,
                "sqlite": EngineCapabilityState.SUPPORTED,
                "mysql": EngineCapabilityState.SUPPORTED,
                "mariadb": EngineCapabilityState.SUPPORTED,
            }
        ),
        MigrationOperationType.ADD_COLUMN: CatalogEntry(
            operation_type=MigrationOperationType.ADD_COLUMN,
            description="Add column to existing table.",
            default_preconditions=[PreconditionType.OBJECT_EXISTENCE],
            engine_capabilities={
                "postgresql": EngineCapabilityState.SUPPORTED,
                "supabase": EngineCapabilityState.SUPPORTED,
                "sqlite": EngineCapabilityState.CONDITIONAL,  # Limited default/null expressions
                "mysql": EngineCapabilityState.SUPPORTED,
                "mariadb": EngineCapabilityState.SUPPORTED,
            },
            engine_limitations={
                "sqlite": ["SQLite restricts ADD COLUMN if column has PRIMARY KEY, UNIQUE, or CURRENT_TIMESTAMP default without constant."]
            }
        ),
        MigrationOperationType.DROP_COLUMN: CatalogEntry(
            operation_type=MigrationOperationType.DROP_COLUMN,
            description="Drop column from table.",
            default_preconditions=[PreconditionType.OBJECT_EXISTENCE, PreconditionType.BACKUP_PRESERVATION_REVIEW],
            engine_capabilities={
                "postgresql": EngineCapabilityState.SUPPORTED,
                "supabase": EngineCapabilityState.SUPPORTED,
                "sqlite": EngineCapabilityState.CONDITIONAL,  # Added in 3.35.0, older requires table rebuild
                "mysql": EngineCapabilityState.SUPPORTED,
                "mariadb": EngineCapabilityState.SUPPORTED,
            },
            engine_limitations={
                "sqlite": ["SQLite DROP COLUMN requires SQLite >= 3.35.0 or full table rebuild."]
            }
        ),
        MigrationOperationType.ALTER_COLUMN_TYPE: CatalogEntry(
            operation_type=MigrationOperationType.ALTER_COLUMN_TYPE,
            description="Alter data type of existing column.",
            default_preconditions=[PreconditionType.OBJECT_EXISTENCE, PreconditionType.DATA_VALIDATION_REQUIRED],
            requires_data_validation=True,
            engine_capabilities={
                "postgresql": EngineCapabilityState.SUPPORTED,
                "supabase": EngineCapabilityState.SUPPORTED,
                "sqlite": EngineCapabilityState.UNSUPPORTED,  # Requires table rebuild
                "mysql": EngineCapabilityState.SUPPORTED,
                "mariadb": EngineCapabilityState.SUPPORTED,
            },
            engine_limitations={
                "sqlite": ["SQLite requires a 12-step table recreation procedure to alter column types."],
                "mysql": ["MySQL ALTER TABLE MODIFY COLUMN locks table unless ALGORITHM=INPLACE is supported for the conversion."],
            }
        ),
        MigrationOperationType.ALTER_COLUMN_NULLABILITY: CatalogEntry(
            operation_type=MigrationOperationType.ALTER_COLUMN_NULLABILITY,
            description="Alter column nullability constraint.",
            default_preconditions=[PreconditionType.OBJECT_EXISTENCE, PreconditionType.DATA_VALIDATION_REQUIRED],
            requires_data_validation=True,
            engine_capabilities={
                "postgresql": EngineCapabilityState.SUPPORTED,
                "supabase": EngineCapabilityState.SUPPORTED,
                "sqlite": EngineCapabilityState.UNSUPPORTED,  # Requires table rebuild
                "mysql": EngineCapabilityState.SUPPORTED,
                "mariadb": EngineCapabilityState.SUPPORTED,
            },
            engine_limitations={
                "sqlite": ["SQLite cannot alter column nullability directly; requires table rebuild."]
            }
        ),
        MigrationOperationType.ALTER_COLUMN_DEFAULT: CatalogEntry(
            operation_type=MigrationOperationType.ALTER_COLUMN_DEFAULT,
            description="Set or drop column default value.",
            default_preconditions=[PreconditionType.OBJECT_EXISTENCE],
            engine_capabilities={
                "postgresql": EngineCapabilityState.SUPPORTED,
                "supabase": EngineCapabilityState.SUPPORTED,
                "sqlite": EngineCapabilityState.UNSUPPORTED,  # Requires table rebuild
                "mysql": EngineCapabilityState.SUPPORTED,
                "mariadb": EngineCapabilityState.SUPPORTED,
            },
            engine_limitations={
                "sqlite": ["SQLite does not support ALTER COLUMN SET DEFAULT; requires table rebuild."]
            }
        ),
        MigrationOperationType.ADD_PRIMARY_KEY: CatalogEntry(
            operation_type=MigrationOperationType.ADD_PRIMARY_KEY,
            description="Add primary key constraint.",
            default_preconditions=[PreconditionType.OBJECT_EXISTENCE, PreconditionType.DATA_VALIDATION_REQUIRED],
            requires_data_validation=True,
            engine_capabilities={
                "postgresql": EngineCapabilityState.SUPPORTED,
                "supabase": EngineCapabilityState.SUPPORTED,
                "sqlite": EngineCapabilityState.UNSUPPORTED,
                "mysql": EngineCapabilityState.SUPPORTED,
                "mariadb": EngineCapabilityState.SUPPORTED,
            },
            engine_limitations={
                "sqlite": ["SQLite requires primary keys to be declared during CREATE TABLE."]
            }
        ),
        MigrationOperationType.DROP_PRIMARY_KEY: CatalogEntry(
            operation_type=MigrationOperationType.DROP_PRIMARY_KEY,
            description="Drop primary key constraint.",
            default_preconditions=[PreconditionType.OBJECT_EXISTENCE, PreconditionType.BACKUP_PRESERVATION_REVIEW],
            engine_capabilities={
                "postgresql": EngineCapabilityState.SUPPORTED,
                "supabase": EngineCapabilityState.SUPPORTED,
                "sqlite": EngineCapabilityState.UNSUPPORTED,
                "mysql": EngineCapabilityState.SUPPORTED,
                "mariadb": EngineCapabilityState.SUPPORTED,
            },
            engine_limitations={
                "sqlite": ["SQLite cannot drop primary keys without table rebuild."]
            }
        ),
        MigrationOperationType.ADD_UNIQUE_CONSTRAINT: CatalogEntry(
            operation_type=MigrationOperationType.ADD_UNIQUE_CONSTRAINT,
            description="Add unique constraint or unique index.",
            default_preconditions=[PreconditionType.OBJECT_EXISTENCE, PreconditionType.DATA_VALIDATION_REQUIRED],
            requires_data_validation=True,
            engine_capabilities={
                "postgresql": EngineCapabilityState.SUPPORTED,
                "supabase": EngineCapabilityState.SUPPORTED,
                "sqlite": EngineCapabilityState.CONDITIONAL,  # Can create UNIQUE INDEX
                "mysql": EngineCapabilityState.SUPPORTED,
                "mariadb": EngineCapabilityState.SUPPORTED,
            },
            engine_limitations={
                "sqlite": ["SQLite adds unique constraints via CREATE UNIQUE INDEX, not ALTER TABLE ADD CONSTRAINT."]
            }
        ),
        MigrationOperationType.DROP_UNIQUE_CONSTRAINT: CatalogEntry(
            operation_type=MigrationOperationType.DROP_UNIQUE_CONSTRAINT,
            description="Drop unique constraint.",
            default_preconditions=[PreconditionType.OBJECT_EXISTENCE],
            engine_capabilities={
                "postgresql": EngineCapabilityState.SUPPORTED,
                "supabase": EngineCapabilityState.SUPPORTED,
                "sqlite": EngineCapabilityState.CONDITIONAL,
                "mysql": EngineCapabilityState.SUPPORTED,
                "mariadb": EngineCapabilityState.SUPPORTED,
            }
        ),
        MigrationOperationType.ADD_FOREIGN_KEY: CatalogEntry(
            operation_type=MigrationOperationType.ADD_FOREIGN_KEY,
            description="Add foreign key constraint.",
            default_preconditions=[PreconditionType.OBJECT_EXISTENCE, PreconditionType.DATA_VALIDATION_REQUIRED, PreconditionType.DEPENDENCY_RESOLUTION],
            requires_data_validation=True,
            engine_capabilities={
                "postgresql": EngineCapabilityState.SUPPORTED,
                "supabase": EngineCapabilityState.SUPPORTED,
                "sqlite": EngineCapabilityState.UNSUPPORTED,  # Requires table rebuild
                "mysql": EngineCapabilityState.SUPPORTED,
                "mariadb": EngineCapabilityState.SUPPORTED,
            },
            engine_limitations={
                "sqlite": ["SQLite foreign keys must be specified at table creation; cannot be added via ALTER TABLE."]
            }
        ),
        MigrationOperationType.DROP_FOREIGN_KEY: CatalogEntry(
            operation_type=MigrationOperationType.DROP_FOREIGN_KEY,
            description="Drop foreign key constraint.",
            default_preconditions=[PreconditionType.OBJECT_EXISTENCE],
            engine_capabilities={
                "postgresql": EngineCapabilityState.SUPPORTED,
                "supabase": EngineCapabilityState.SUPPORTED,
                "sqlite": EngineCapabilityState.UNSUPPORTED,
                "mysql": EngineCapabilityState.SUPPORTED,
                "mariadb": EngineCapabilityState.SUPPORTED,
            },
            engine_limitations={
                "sqlite": ["SQLite cannot drop foreign key constraints via ALTER TABLE."]
            }
        ),
        MigrationOperationType.ADD_CHECK_CONSTRAINT: CatalogEntry(
            operation_type=MigrationOperationType.ADD_CHECK_CONSTRAINT,
            description="Add check constraint.",
            default_preconditions=[PreconditionType.OBJECT_EXISTENCE, PreconditionType.DATA_VALIDATION_REQUIRED],
            requires_data_validation=True,
            engine_capabilities={
                "postgresql": EngineCapabilityState.SUPPORTED,
                "supabase": EngineCapabilityState.SUPPORTED,
                "sqlite": EngineCapabilityState.UNSUPPORTED,
                "mysql": EngineCapabilityState.SUPPORTED,
                "mariadb": EngineCapabilityState.SUPPORTED,
            }
        ),
        MigrationOperationType.DROP_CHECK_CONSTRAINT: CatalogEntry(
            operation_type=MigrationOperationType.DROP_CHECK_CONSTRAINT,
            description="Drop check constraint.",
            default_preconditions=[PreconditionType.OBJECT_EXISTENCE],
            engine_capabilities={
                "postgresql": EngineCapabilityState.SUPPORTED,
                "supabase": EngineCapabilityState.SUPPORTED,
                "sqlite": EngineCapabilityState.UNSUPPORTED,
                "mysql": EngineCapabilityState.SUPPORTED,
                "mariadb": EngineCapabilityState.SUPPORTED,
            }
        ),
        MigrationOperationType.CREATE_INDEX: CatalogEntry(
            operation_type=MigrationOperationType.CREATE_INDEX,
            description="Create index.",
            default_preconditions=[PreconditionType.OBJECT_EXISTENCE, PreconditionType.OBJECT_ABSENCE],
            engine_capabilities={
                "postgresql": EngineCapabilityState.SUPPORTED,
                "supabase": EngineCapabilityState.SUPPORTED,
                "sqlite": EngineCapabilityState.SUPPORTED,
                "mysql": EngineCapabilityState.SUPPORTED,
                "mariadb": EngineCapabilityState.SUPPORTED,
            }
        ),
        MigrationOperationType.DROP_INDEX: CatalogEntry(
            operation_type=MigrationOperationType.DROP_INDEX,
            description="Drop index.",
            default_preconditions=[PreconditionType.OBJECT_EXISTENCE],
            engine_capabilities={
                "postgresql": EngineCapabilityState.SUPPORTED,
                "supabase": EngineCapabilityState.SUPPORTED,
                "sqlite": EngineCapabilityState.SUPPORTED,
                "mysql": EngineCapabilityState.SUPPORTED,
                "mariadb": EngineCapabilityState.SUPPORTED,
            }
        ),
        MigrationOperationType.MODIFY_INDEX: CatalogEntry(
            operation_type=MigrationOperationType.MODIFY_INDEX,
            description="Modify index definition (typically DROP then CREATE).",
            default_preconditions=[PreconditionType.OBJECT_EXISTENCE],
            engine_capabilities={
                "postgresql": EngineCapabilityState.CONDITIONAL,
                "supabase": EngineCapabilityState.CONDITIONAL,
                "sqlite": EngineCapabilityState.CONDITIONAL,
                "mysql": EngineCapabilityState.CONDITIONAL,
                "mariadb": EngineCapabilityState.CONDITIONAL,
            }
        ),
        MigrationOperationType.CREATE_VIEW: CatalogEntry(
            operation_type=MigrationOperationType.CREATE_VIEW,
            description="Create view definition.",
            default_preconditions=[PreconditionType.DEPENDENCY_RESOLUTION, PreconditionType.OBJECT_ABSENCE],
            engine_capabilities={
                "postgresql": EngineCapabilityState.SUPPORTED,
                "supabase": EngineCapabilityState.SUPPORTED,
                "sqlite": EngineCapabilityState.SUPPORTED,
                "mysql": EngineCapabilityState.SUPPORTED,
                "mariadb": EngineCapabilityState.SUPPORTED,
            }
        ),
        MigrationOperationType.DROP_VIEW: CatalogEntry(
            operation_type=MigrationOperationType.DROP_VIEW,
            description="Drop view definition.",
            default_preconditions=[PreconditionType.OBJECT_EXISTENCE],
            engine_capabilities={
                "postgresql": EngineCapabilityState.SUPPORTED,
                "supabase": EngineCapabilityState.SUPPORTED,
                "sqlite": EngineCapabilityState.SUPPORTED,
                "mysql": EngineCapabilityState.SUPPORTED,
                "mariadb": EngineCapabilityState.SUPPORTED,
            }
        ),
        MigrationOperationType.MODIFY_VIEW: CatalogEntry(
            operation_type=MigrationOperationType.MODIFY_VIEW,
            description="Modify or replace view definition.",
            default_preconditions=[PreconditionType.OBJECT_EXISTENCE, PreconditionType.DEPENDENCY_RESOLUTION],
            engine_capabilities={
                "postgresql": EngineCapabilityState.SUPPORTED,
                "supabase": EngineCapabilityState.SUPPORTED,
                "sqlite": EngineCapabilityState.CONDITIONAL,  # Requires DROP and CREATE
                "mysql": EngineCapabilityState.SUPPORTED,
                "mariadb": EngineCapabilityState.SUPPORTED,
            }
        ),
    }

    @classmethod
    def get_entry(cls, op_type: MigrationOperationType) -> CatalogEntry:
        """Retrieve catalog entry for operation type."""
        return cls._ENTRIES[op_type]

    @classmethod
    def get_engine_capability(cls, op_type: MigrationOperationType, engine: str) -> EngineCapabilityState:
        """Query engine capability for operation."""
        norm_engine = engine.lower()
        entry = cls.get_entry(op_type)
        return entry.engine_capabilities.get(norm_engine, EngineCapabilityState.SUPPORTED)

    @classmethod
    def get_engine_limitations(cls, op_type: MigrationOperationType, engine: str) -> List[str]:
        """Query engine specific limitations."""
        norm_engine = engine.lower()
        entry = cls.get_entry(op_type)
        return entry.engine_limitations.get(norm_engine, [])
