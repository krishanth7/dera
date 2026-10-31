# Future NoSQL Maintainability Compatibility

## Architectural Vision

While Phase 8.4 focuses on verified relational engines (PostgreSQL, Supabase PostgreSQL, SQLite, MySQL, MariaDB), DERA's maintainability metric models and rule interfaces are engineered for future NoSQL support (MongoDB, DynamoDB, Firestore, Firebase Realtime Database, Cosmos DB).

## Capability Matrix & Semantic Adaptations

| Relational Diagnostic | NoSQL Analogue | Applicability Strategy |
| :--- | :--- | :--- |
| `DERA-MNT-001` (Table Width) | Document Field Depth / Count | Replaced by root document property count and nesting depth limits. Wide flat documents often indicate missing sub-document nesting. |
| `DERA-MNT-002` (Nullability) | Field Sparsity / Schema Drift | NoSQL schemas are schema-on-read; nullability is replaced by attribute presence ratio across sampled documents. |
| `DERA-MNT-003` (Naming Style) | Collection & Property Naming | Directly applicable. Evaluates JSON property naming conventions (e.g. `camelCase` for MongoDB/Firestore). |
| `DERA-MNT-004` (Reserved Words) | Engine BSON / SDK Keywords | Evaluates engine-reserved operators (`$`, `_id`, partition key keywords in DynamoDB). |
| `DERA-MNT-005` (Namespace) | Database / Collection Imbalance | Evaluates collection distribution across logical databases. |
| `DERA-MNT-006` (Coupling) | Denormalization & Reference Fan-In | Evaluates DBRef or manual ID reference coupling across collections. |
| `DERA-MNT-007` (Dependencies) | Cross-Document Circular References | Detects circular references in relational embeddings or references. |
| `DERA-MNT-008` (LOB Types) | Large Binary / GridFS Overflow | Detects oversized BSON payloads approaching the 16MB limit in MongoDB or 400KB in DynamoDB. |

## Guardrail

Relational maintainability rules must **never** be applied indiscriminately to NoSQL engines. Engine capability profiles must declare support before rules are scheduled.
