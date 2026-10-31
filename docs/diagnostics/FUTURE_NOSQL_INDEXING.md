# Extensibility: Future NoSQL and Cloud Database Indexing

## 1. Overview
While Phase 8.2 concentrates on verified relational connectors (PostgreSQL, Supabase PostgreSQL, SQLite, MySQL, and MariaDB), the signature and rule architecture is designed to accommodate future document and key-value databases without schema model breakage.

## 2. Planned NoSQL Engine Adaptations
- **Firebase Firestore / MongoDB**:
  - Single-field indexing vs Composite index requirement models.
  - Absence of relational foreign key constraints; relational constraint rules yield `ApplicabilityStatus.NOT_APPLICABLE`.
  - Array and map term indexing semantics (`ASCENDING`, `DESCENDING`, `GEO2D`, `TEXT`).
- **Amazon DynamoDB**:
  - Global Secondary Indexes (GSI) and Local Secondary Indexes (LSI) with projection attributes (`ALL`, `KEYS_ONLY`, `INCLUDE`).
  - Partition Key and Sort Key leading prefix analysis.
- **Azure Cosmos DB**:
  - Automatic indexing path policies (`/*`, `includedPaths`, `excludedPaths`).
