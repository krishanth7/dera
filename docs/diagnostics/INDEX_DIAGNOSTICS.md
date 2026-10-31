# DERA Phase 8.2 — Index & Constraint Diagnostics Overview

## 1. Engineering Mission
DERA Phase 8.2 introduces deterministic index and constraint intelligence into the Phase 8 diagnostic engine. Operating strictly in read-only analysis over canonical schema representations and snapshots, Phase 8.2 detects structurally provable duplicate definitions, identifies candidate redundancy in composite index prefixes, audits foreign key index coverage, and validates relational constraints (Primary Key, Foreign Key, Unique, and Check constraints).

## 2. Core Architectural Guarantees
- **Strictly Read-Only**: Performs static inspection without executing customer DDL or mutations.
- **Zero AI/LLM/ML**: All rule evaluations rely exclusively on deterministic set algebra, graph references, and canonical signatures.
- **Engine-Specific Semantics**: Respects native database behavior across PostgreSQL, Supabase PostgreSQL, SQLite, MySQL, and MariaDB (e.g., InnoDB automatic foreign key indexing, partial index support, and operator classes).
- **Constraint Ownership Safety**: Distinguishes secondary user indexes from engine-managed primary key and unique constraint backing indexes, preventing hazardous drops.
- **Explainable Evidence**: Every finding carries structured metadata, field comparisons, and deterministic SHA-256 fingerprints.

## 3. Rule Catalog Overview

| Rule ID | Title | Category | Severity | Target Object |
| :--- | :--- | :--- | :--- | :--- |
| `DERA-IDX-001` | Exact Duplicate Index Definition | INDEXES | MEDIUM | `TableIndex` |
| `DERA-IDX-002` | Potentially Redundant B-Tree Index (Leftmost Prefix) | INDEXES | LOW | `TableIndex` |
| `DERA-IDX-003` | Foreign Key Supporting Index Coverage | INDEXES | MEDIUM | `ForeignKey` |
| `DERA-IDX-004` | Index Column Reference Integrity | INDEXES | HIGH | `TableIndex` |
| `DERA-CON-001` | Primary Key Structural Integrity | CONSTRAINTS | HIGH | `PrimaryKey` |
| `DERA-CON-002` | Foreign Key Referential Mapping Integrity | CONSTRAINTS | HIGH / LOW | `ForeignKey` |
| `DERA-CON-003` | Unique Constraint Structural Integrity | CONSTRAINTS | MEDIUM / LOW | `UniqueConstraint` |
| `DERA-CON-004` | Check Constraint Metadata Integrity | CONSTRAINTS | HIGH / MEDIUM | `CheckConstraint` |
| `DERA-CON-005` | Constraint Column Integrity | CONSTRAINTS | HIGH | `Constraint` |
