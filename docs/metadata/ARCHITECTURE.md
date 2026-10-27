# Metadata Normalization & Identity Architecture

**Subsystem:** `dera.metadata` / `dera_metadata`  
**Contract Version:** `1.0.0`  

---

## 1. Architectural Boundaries

Phase 5.5 sits between the database connector layer (Phase 5.1–5.4) and the reverse engineering engine (Phase 6):

```text
+-------------------------------------------------------------------------------+
|                      Phase 5.1-5.4 Database Connectors                        |
|       (PostgreSQL, Supabase PostgreSQL, SQLite, MySQL, MariaDB)               |
+-------------------------------------------------------------------------------+
                                       |
                                       v (Universal DatabaseMetadataReport)
+-------------------------------------------------------------------------------+
|                      Phase 5.5 Normalization Pipeline                         |
|                                                                               |
|   1. Input Report Validation & Capability Extraction                          |
|   2. Engine Adapter Selection (Postgres, SQLite, MySQL, MariaDB)              |
|   3. Identifier Parsing & Unquoting (Preserving Native Declared Case)         |
|   4. Canonical Type Classification & Attribute Preservation                   |
|   5. Cryptographic Stable Object ID Generation (SHA-256 Digest)               |
|   6. Referential Integrity Validation & Collision Detection                   |
|   7. Multi-Level Deterministic Sorting                                        |
|   8. Canonical JSON Serialization & SHA-256 Digest Computation                |
+-------------------------------------------------------------------------------+
                                       |
                                       v (Immutable CanonicalDatabase Model)
+-------------------------------------------------------------------------------+
|                         Phase 6 Reverse Engineering                           |
|       (Dependency DAG, Tarjan's Cycle Detection, Schema Fingerprints)         |
+-------------------------------------------------------------------------------+
```

---

## 2. Component Structure

- **`models/`**: Strongly typed, frozen Pydantic v2 domain models representing databases, namespaces, tables, columns, constraints, foreign keys, indexes, views, and triggers.
- **`adapters/`**: Engine-specific type categorization and feature extraction rules for PostgreSQL, SQLite, MySQL, and MariaDB.
- **`identity.py`**: Length-prefixed SHA-256 stable `ObjectId` computation and unnamed constraint surrogate generation.
- **`identifiers.py`**: Case-folding lookup rules and unquoting utilities across dialects.
- **`ordering.py`**: Multi-key deterministic sorting routines.
- **`validation.py`**: Reference integrity, unique identity validation, and memory/payload limit enforcement.
- **`serialization.py`**: Canonical UTF-8 JSON serialization and deterministic schema hashing.
