# DERA Diagnostics — Extensibility & Future NoSQL Rules

**Milestone:** Phase 8.1 — Deterministic Schema Diagnostic Rules Engine  
**Status:** Architectural Blueprint  

---

## 1. Overview

While Phase 8.1 validates relational database engines (PostgreSQL, Supabase, SQLite, MySQL, MariaDB), the diagnostic architecture is designed to support future non-relational document databases without architectural redesign:
- Firebase Firestore
- Firebase Realtime Database
- MongoDB
- DynamoDB
- Azure Cosmos DB

---

## 2. Applicability & Flexibility Invariants

1. **Non-Enforcement of Relational Constraints on Document Models:**
   - Rules declaring `required_capabilities=("foreign_keys",)` or `supported_object_kinds=("table",)` will automatically evaluate to `NOT_APPLICABLE` or `UNSUPPORTED` for document collections.
   - Relational rules will never falsely flag NoSQL document collections for lacking primary keys or foreign keys.
2. **Document-Specific Rule Categories:**
   - Future milestones will introduce rule categories tailored to document structures:
     - `DOCUMENT_SHAPE`: Polymorphic schema drift across document collections.
     - `NESTING_DEPTH`: Excessive subcollection or embedded document nesting depth.
     - `INDEX_COVERAGE`: Single-field and composite index gaps in query paths.
     - `HOTSPOTTING`: Partition key distribution anomalies.
