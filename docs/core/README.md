# DERA Deterministic Core Engine Documentation

> **Package:** `packages/core`  
> **Runtime:** Python 3.12+ (Pure Standard Library)  
> **Status:** Implemented & Production-Ready  
> **Maintainer:** Krishanth  
> **Last Verified:** 2026-10-26 (Commit `e550fdd`)  

---

## 1. Core Engine Purpose & Scope

The **DERA Core Engine** (`packages/core`) is the algorithmic foundation of DERA. It contains engine-agnostic database schema representations, topological dependency sorting algorithms, rule-based diagnostic linters, and cryptographic SHA-256 schema hashing.

In strict accordance with DERA's foundational charter:
- **Pure Standard Library:** Zero third-party runtime dependencies. The core depends exclusively on standard Python modules (`dataclasses`, `hashlib`, `json`, `datetime`, `typing`, `enum`, `abc`).
- **Strictly Non-AI:** Contains zero probabilistic inference, zero LLM models, and zero embeddings.
- **Mathematical Determinism:** Operations yield identical, reproducible results across platforms, architectures, and operating systems.

---

## 2. Namespace Organization & Roles

`packages/core/src` houses two distinct Python package namespaces:

| Namespace | Active Modules | Responsibilities & Contents |
|---|---|---|
| `dera` | [`models.py`](../../packages/core/src/dera/models.py)<br/>[`graph.py`](../../packages/core/src/dera/graph.py)<br/>[`diagnostics/__init__.py`](../../packages/core/src/dera/diagnostics/__init__.py) | Canonical domain models (`DatabaseTable`, `Column`, `SchemaSnapshot`), graph adjacency and Kahn's topological sort, and rule-based diagnostic linting. |
| `dera_core` | [`exceptions.py`](../../packages/core/src/dera_core/exceptions.py) | Structured domain exception hierarchy (`DeraError`, `CycleDetectedError`, `ReadOnlyViolationError`, `SchemaParsingError`, `DiagnosticRuleError`). |

> **Note on Technical Debt:** In Phase 3, these namespaces will be consolidated into a single unified `dera` namespace while maintaining backward-compatible re-exports in `dera_core`.

---

## 3. Canonical Domain Models (`dera.models`)

All schema representations are modeled as frozen, immutable Python dataclasses:

### 3.1 `DatabaseColumn` (alias `Column`)
Represents an individual column within a table:
- `name: str`: Column identifier.
- `data_type: str`: Engine-agnostic canonical data type (e.g. `INTEGER`, `VARCHAR(255)`, `TIMESTAMP`).
- `is_nullable: bool = True`: Whether NULL values are permitted.
- `default_expression: str | None = None`: Default value expression.
- `ordinal_position: int = 1`: 1-based column position.
- `character_maximum_length: int | None = None`: Maximum character length.
- `numeric_precision: int | None = None`: Total count of significant digits.
- `numeric_scale: int | None = None`: Count of fractional digits.
- `description: str | None = None`: Column comment or documentation.

### 3.2 `PrimaryKeyConstraint`
Represents an explicit primary key constraint:
- `name: str`: Constraint identifier.
- `columns: tuple[str, ...]`: Ordered tuple of column names comprising the primary key.

### 3.3 `ForeignKeyConstraint` (alias `ForeignKey`)
Represents a referential integrity foreign-key relationship:
- `name: str`: Constraint identifier.
- `source_columns: tuple[str, ...]`: Columns in referencing table.
- `target_schema: str`: Target schema name (e.g. `public`).
- `target_table: str`: Referenced table name.
- `target_columns: tuple[str, ...]`: Referenced columns in target table.
- `on_update: str = "NO ACTION"`: Referential update action.
- `on_delete: str = "NO ACTION"`: Referential delete action.

### 3.4 `TableIndex` (alias `Index`)
Represents an index defined on a database table:
- `name: str`: Index identifier.
- `columns: tuple[str, ...]`: Indexed columns in order.
- `is_unique: bool = False`: Unique constraint flag.
- `index_type: str = "BTREE"`: Index access method.
- `predicate: str | None = None`: Partial index WHERE filter expression.

### 3.5 `DatabaseTable` (alias `Table`)
Represents a database table along with its columns, constraints, and indexes:
- `schema: str`: Schema or namespace (e.g. `public`, `main`).
- `name: str`: Table identifier.
- `columns: tuple[DatabaseColumn, ...]`: Contained columns.
- `primary_key: PrimaryKeyConstraint | None = None`: Primary key constraint.
- `foreign_keys: tuple[ForeignKeyConstraint, ...]`: Foreign key constraints.
- `indexes: tuple[TableIndex, ...]`: Defined indexes.
- `fully_qualified_name -> str`: Helper returning `f"{schema}.{name}"`.
- `column_names -> tuple[str, ...]`: Helper returning column name list.

### 3.6 `SchemaSnapshot`
Represents an immutable, versioned snapshot of an inspected database schema:
- `database_name: str`: Target database identifier.
- `engine: str`: Database dialect (e.g. `sqlite`, `postgresql`).
- `tables: tuple[DatabaseTable, ...]`: Ordered collection of tables.
- `created_at: datetime`: UTC timestamp of snapshot creation.
- `snapshot_id: str`: Optional unique identifier.
- `compute_hash() -> str`: Computes a deterministic SHA-256 fingerprint of the entire schema structure by serializing a sorted canonical dictionary.

---

## 4. Rule-Based Diagnostic Engine (`dera.diagnostics`)

The diagnostic engine evaluates database tables against reproducible static engineering rules to flag structural anti-patterns:

| Rule ID | Severity | Category | Target Condition | Remediation |
|---|---|---|---|---|
| `RULE-INT-001` | `RuleSeverity.ERROR` | Integrity | Table lacks an explicit primary key constraint. | `ALTER TABLE <table_fqn> ADD PRIMARY KEY (<id_column>);` |
| `RULE-PERF-002` | `RuleSeverity.WARNING` | Performance | Foreign key constraint lacks a supporting index starting with the foreign key's leading column. | `CREATE INDEX idx_<table_name>_<col> ON <table_fqn> (<cols>);` |

### Diagnostic Execution
```python
from dera.diagnostics import run_all_diagnostics

findings = run_all_diagnostics(snapshot.tables)
for f in findings:
    print(f"[{f.severity}] {f.table}: {f.message}")
    if f.remediation_ddl:
        print(f"  Remediation: {f.remediation_ddl}")
```

---

## 5. Domain Exception Hierarchy (`dera_core.exceptions`)

All exceptions inherit from `DeraError`:

```text
DeraError (Base domain exception with message and details dict)
├── SchemaParsingError (DDL parsing or metadata extraction failure)
├── CycleDetectedError (Circular dependency in foreign-key graph)
├── DiagnosticRuleError (Internal rule evaluation failure)
├── ConfigurationError (Environment or platform config error)
└── ConnectorError (Base database connector exception)
    ├── ReadOnlyViolationError (Mutation SQL intercepted and rejected)
    └── ConnectionAuthenticationError (Database connection failed)
```

---

## 6. Test Coverage & Verification

Core functionality is verified through comprehensive test suites:
- **Unit Tests:** `tests/unit/test_models.py` validates model instantiation, primary/foreign key creation, SHA-256 hashing stability, and diagnostic rule evaluation.
- **Regression Tests:** `tests/regression/test_schema_regression.py` validates that schema snapshot hashes remain bit-for-bit invariant across runs.
- **Architecture Tests:** `tests/architecture/test_module_boundaries.py` asserts that `packages/core` never imports web frameworks or AI libraries.

Execute core tests:
```bash
python -m unittest tests/unit/test_models.py
```

---

## 7. Related Documentation

- [Graph Engine Architecture & Algorithms](GRAPH_ENGINE.md)
- [System Architecture Overview](../architecture/SYSTEM_OVERVIEW.md)
- [Shared Schema Contracts](../contracts/SCHEMA_CONTRACTS.md)
- [Database Connector Architecture](../connectors/CONNECTOR_ARCHITECTURE.md)
