# DERA Phase 8.3 — Future NoSQL & Cloud Relationship Extensibility

## 1. Context & Extensibility
While Phase 8.3 focuses strictly on verified relational database metadata (PostgreSQL, Supabase PostgreSQL, SQLite, MySQL, MariaDB), its architecture is designed for forward compatibility with non-relational document and key-value datastores (Firebase Firestore, MongoDB, AWS DynamoDB, Azure Cosmos DB, Google Cloud Datastore).

## 2. Inferred vs. Declared References
- **Relational Databases**: Relationships are explicitly declared via schema-level `FOREIGN KEY` constraints enforced by the database engine.
- **NoSQL / Document Stores**: Relationships are typically implicit (e.g., embedded documents, reference IDs like `customerId` string fields, or DBRefs).

### Extensibility Rules
1. **Never Fabricate Foreign Keys**: Implicit NoSQL references must never be represented as verified relational foreign keys.
2. **Capability Flagging**: Engines without foreign key constraints declare `supports_foreign_keys = False` in `GraphCapabilityProfile`, causing relationship integrity rules to report `EvaluationStatus.UNSUPPORTED` cleanly.
3. **Observed Reference Metadata**: Future phases may introduce an `ObservedReferenceGraph` for document datastores, analyzed under separate non-relational diagnostic rulesets.
