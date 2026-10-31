# DERA Metadata Normalization & Identity Subsystem

**Subsystem:** `dera.metadata` / `dera_metadata`  
**Milestone:** Phase 5.5 — Metadata Normalization & Identity  
**Status:** Complete & Production-Ready  
**Contract Version:** `1.0.0`  

---

## 1. Overview

The DERA Canonical Metadata Normalization & Identity subsystem provides deterministic, strongly typed, and auditable normalization of schema metadata extracted by database connectors across PostgreSQL, Supabase PostgreSQL, SQLite, MySQL, and MariaDB.

It acts as the canonical bridge between raw connector inspection reports and downstream dependency graph analysis, schema comparison, and reverse-engineering engines.

---

## 2. Key Principles

1. **Zero AI/LLM Integration:** 100% deterministic, explainable rule-based catalog classification.
2. **Native Semantics Preservation:** Full native engine data types, expressions, collations, and storage modes are retained alongside canonical categories.
3. **Cryptographic Object Identity:** Every database object receives a unique, collision-resistant `ObjectId` computed via SHA-256 over length-prefixed canonical components.
4. **Deterministic Sorting:** Collections are sorted by strict multi-key algorithms, ensuring byte-level reproducible output regardless of database catalog query return order.
5. **Auditable Provenance:** Every normalized object tracks source engine, source version, collection timestamp, connector version, and completeness status.

---

## 3. Quickstart Example

```python
from dera_connectors.metadata import DatabaseMetadataReport, SchemaInfo, TableInfo, ColumnInfo
from dera.metadata import (
    MetadataNormalizer,
    serialize_canonical_database,
    compute_canonical_database_hash,
)

# 1. Instantiate the Normalizer for the target dialect
normalizer = MetadataNormalizer(
    engine="postgresql",
    database_name="production",
    server_version="16.2",
    workspace_id="ws_retail",
)

# 2. Ingest universal metadata report
canonical_db = normalizer.normalize(report)

# 3. Access strongly-typed canonical hierarchy
for ns in canonical_db.namespaces:
    print(f"Namespace: {ns.name} (id={ns.id})")
    for tbl in ns.tables:
        print(f"  Table: {tbl.name} (id={tbl.id})")
        for col in tbl.columns:
            print(f"    Column: {col.name} -> {col.canonical_type.value}")

# 4. Generate deterministic UTF-8 JSON & SHA-256 digest
json_str = serialize_canonical_database(canonical_db, indent=2)
schema_fingerprint = compute_canonical_database_hash(canonical_db)
print(f"Canonical Digest: {schema_fingerprint}")
```

---

## 4. Documentation Index

- [Architecture & Data Flow](ARCHITECTURE.md)
- [Canonical Contracts & Models](CANONICAL_CONTRACTS.md)
- [Stable Object Identity Formulation](OBJECT_IDENTITY.md)
- [Dialect Identifier Rules](IDENTIFIER_RULES.md)
- [Type Normalization Taxonomy](TYPE_NORMALIZATION.md)
- [Constraint Normalization](CONSTRAINT_NORMALIZATION.md)
- [Index Normalization](INDEX_NORMALIZATION.md)
- [Provenance & Auditing](PROVENANCE.md)
- [Capability Mapping](CAPABILITY_MAPPING.md)
- [Contract Versioning Policy](CONTRACT_VERSIONING.md)
- [Security & Resource Boundaries](SECURITY.md)
- [Testing & Golden Files](TESTING.md)
- [Dialect Compatibility Matrix](COMPATIBILITY.md)
