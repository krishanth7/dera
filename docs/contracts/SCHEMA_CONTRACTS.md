# DERA Shared Schema Contracts & Protocol Definitions

> **Package:** `packages/contracts`  
> **Status:** Implemented & Verified  
> **Maintainer:** Krishanth  
> **Last Verified:** 2026-10-26 (Commit `e550fdd`)  

---

## 1. Overview & Synchronization Strategy

The **DERA Contracts Package** (`packages/contracts`) provides shared protocol definitions and data exchange schemas used across the DERA monorepo.

To prevent drift between Python backend services and TypeScript frontend studios:
1. **JSON Schema as Exchange Specification:** [`packages/contracts/schemas/schema-snapshot.json`](../../packages/contracts/schemas/schema-snapshot.json) defines the formal wire format for serialized schema snapshots.
2. **TypeScript Interfaces:** [`packages/contracts/src/index.ts`](../../packages/contracts/src/index.ts) exports type-safe interfaces for frontend visualizers and API clients.
3. **Python Dataclass Parity:** [`packages/core/src/dera/models.py`](../../packages/core/src/dera/models.py) implements corresponding Python dataclasses with identical field semantics and deterministic serialization.

> **Synchronization Notice:** Schema synchronization is currently maintained via shared code standards and verified by automated unit tests and TypeScript compiler checks (`tsc --noEmit`). Automated cross-language code generation is planned for future phases.

---

## 2. Canonical Type Mapping & Correspondence

The table below maps Python core domain models to shared TypeScript interfaces and JSON Schema constructs:

| Entity | Python Core Dataclass (`dera.models`) | TypeScript Interface (`@dera/contracts`) | JSON Schema Definition |
|---|---|---|---|
| **Column** | `DatabaseColumn` | `DatabaseColumn` | `SchemaSnapshot.properties.tables.items.properties.columns.items` |
| **Primary Key** | `PrimaryKeyConstraint` | `PrimaryKeyConstraint` | `SchemaSnapshot.properties.tables.items.properties.primary_key` |
| **Foreign Key** | `ForeignKeyConstraint` | `ForeignKeyConstraint` | `SchemaSnapshot.properties.tables.items.properties.foreign_keys.items` |
| **Index** | `TableIndex` | `TableIndex` | `SchemaSnapshot.properties.tables.items.properties.indexes.items` |
| **Table** | `DatabaseTable` | `DatabaseTable` | `SchemaSnapshot.properties.tables.items` |
| **Snapshot** | `SchemaSnapshot` | `SchemaSnapshot` | Root Object (`title: "SchemaSnapshot"`) |
| **Finding** | `DiagnosticFinding` (`dera.diagnostics`) | `DiagnosticFinding` | — |
| **Graph** | `dict[str, set[str]]` (`dera.graph`) | `TableDependencyGraph` | — |

---

## 3. Detailed Data Structures

### 3.1 `DatabaseColumn`
Represents an individual column within a table.

| Field Name | TypeScript Type | Python Type | Required? | Nullable? | Description |
|---|---|---|---|---|---|
| `name` | `string` | `str` | **Yes** | No | Column name identifier |
| `data_type` | `string` | `str` | **Yes** | No | Canonical data type (e.g. `INTEGER`, `VARCHAR(255)`) |
| `is_nullable` / `nullable` | `boolean` | `bool` | **Yes** | No | Whether NULL values are accepted (default `true`) |
| `default_expression` / `default_value` | `string \| null` | `str \| None` | Optional | Yes | Default column expression |
| `ordinal_position` | `number` | `int` | Optional | No | 1-based column position in table |

### 3.2 `PrimaryKeyConstraint`
Represents a primary key constraint.

| Field Name | TypeScript Type | Python Type | Required? | Nullable? | Description |
|---|---|---|---|---|---|
| `name` | `string` | `str` | **Yes** | No | Primary key constraint name |
| `columns` | `string[]` | `tuple[str, ...]` | **Yes** | No | Ordered list of primary key columns |

### 3.3 `ForeignKeyConstraint`
Represents referential integrity constraints.

| Field Name | TypeScript Type | Python Type | Required? | Nullable? | Description |
|---|---|---|---|---|---|
| `name` | `string` | `str` | **Yes** | No | Foreign key constraint name |
| `source_columns` | `string[]` | `tuple[str, ...]` | **Yes** | No | Referencing columns in this table |
| `target_schema` | `string` | `str` | Optional | No | Target schema (e.g. `public`) |
| `target_table` | `string` | `str` | **Yes** | No | Referenced table name |
| `target_columns` | `string[]` | `tuple[str, ...]` | **Yes** | No | Referenced column names in target table |
| `on_update` | `string` | `str` | Optional | No | Update action (`NO ACTION`, `CASCADE`, `RESTRICT`) |
| `on_delete` | `string` | `str` | Optional | No | Delete action (`NO ACTION`, `CASCADE`, `RESTRICT`) |

### 3.4 `TableIndex`
Represents an index defined on a database table.

| Field Name | TypeScript Type | Python Type | Required? | Nullable? | Description |
|---|---|---|---|---|---|
| `name` | `string` | `str` | **Yes** | No | Index name |
| `columns` | `string[]` | `tuple[str, ...]` | **Yes** | No | Indexed columns in order |
| `is_unique` | `boolean` | `bool` | **Yes** | No | Unique index flag |
| `index_type` | `string` | `str` | Optional | No | Index method (`BTREE`, `HASH`, `GIN`) |

---

## 4. Validated Example Exchange Payload

The JSON payload below satisfies the canonical JSON Schema in `packages/contracts/schemas/schema-snapshot.json`:

```json
{
  "database_name": "ecommerce_db",
  "engine": "sqlite",
  "version": "0.1.0",
  "created_at": "2026-10-26T12:00:00Z",
  "tables": [
    {
      "schema": "main",
      "name": "users",
      "columns": [
        {
          "name": "id",
          "data_type": "INTEGER",
          "is_nullable": false,
          "default_expression": null
        },
        {
          "name": "email",
          "data_type": "VARCHAR(255)",
          "is_nullable": false,
          "default_expression": null
        }
      ],
      "primary_key": {
        "name": "pk_users",
        "columns": ["id"]
      },
      "foreign_keys": [],
      "indexes": [
        {
          "name": "idx_users_email",
          "columns": ["email"],
          "is_unique": true,
          "index_type": "BTREE"
        }
      ]
    },
    {
      "schema": "main",
      "name": "orders",
      "columns": [
        {
          "name": "id",
          "data_type": "INTEGER",
          "is_nullable": false,
          "default_expression": null
        },
        {
          "name": "user_id",
          "data_type": "INTEGER",
          "is_nullable": false,
          "default_expression": null
        }
      ],
      "primary_key": {
        "name": "pk_orders",
        "columns": ["id"]
      },
      "foreign_keys": [
        {
          "name": "fk_orders_user",
          "source_columns": ["user_id"],
          "target_schema": "main",
          "target_table": "users",
          "target_columns": ["id"],
          "on_update": "NO ACTION",
          "on_delete": "CASCADE"
        }
      ],
      "indexes": [
        {
          "name": "idx_orders_user_id",
          "columns": ["user_id"],
          "is_unique": false,
          "index_type": "BTREE"
        }
      ]
    }
  ]
}
```

---

## 5. Verification & Type Checking

To verify shared contracts across TypeScript workspaces:
```bash
npx -p typescript tsc --noEmit
```

To run complete development suite checks:
```bash
python scripts/development/dev.py all
```

---

## 6. Related Documentation

- [Contracts Documentation Hub](README.md)
- [Core Domain Models](../core/README.md)
- [Backend API Contracts](../backend/API_CONTRACTS.md)
- [Frontend Architecture](../frontend/APPLICATION_ARCHITECTURE.md)
