# Universal Object Inspector & Future NoSQL Extensibility

**Module**: `apps/web/src/components/table-inspector/types.ts`  
**Phase**: 7.5 — Table Inspector, Advanced Search & Dependency Visualization  

---

## 1. Architectural Vision

While Phase 7.5 focuses on verified relational database engines (PostgreSQL, SQLite, MySQL, MariaDB), DERA's long-term roadmap encompasses non-relational and cloud data architectures, including:

- **Document Stores**: MongoDB, Firestore, Couchbase.
- **Key-Value & Wide-Column**: DynamoDB, Cassandra, Bigtable.
- **Cloud Native Infrastructure**: Firebase Realtime Database, Supabase Storage buckets.

To ensure long-term architectural stability without requiring wholesale rewrites or misrepresenting document collections as relational tables, Phase 7.5 introduces the **Universal Object Inspector** abstraction.

---

## 2. Universal Object Inspector Interface

The core presentation contract is defined in `apps/web/src/components/table-inspector/types.ts`:

```typescript
export type InspectorObjectKind =
  | "table"
  | "view"
  | "materialized_view"
  | "collection"        // MongoDB / Firestore
  | "document_type"     // Document models
  | "database_resource"; // DynamoDB / Cloud resources

export interface InspectorObject {
  id: string;
  kind: InspectorObjectKind;
  displayName: string;
  namespace?: string;
  completeness: "COMPLETE" | "PARTIAL" | "RESTRICTED" | "UNSUPPORTED" | "UNKNOWN";
  sourceEngine?: string;
  engineDetails?: Record<string, unknown>;
  fieldCount?: number;
  itemCountEstimated?: number;
}
```

---

## 3. Strict Distinctions: Relational vs. Document Models

DERA enforces strict semantic boundaries between relational and non-relational metadata:

| Relational Invariant (Phase 6–7) | Document Store Invariant (Future) | DERA Governance Rule |
| :--- | :--- | :--- |
| **Strict Physical Schema** | Schema-on-Read / Dynamic Schema | Document stores must not display artificial fixed column ordinals. |
| **Enforced Foreign Keys** | Application References / Embedded Docs | Never fabricate SQL foreign keys for MongoDB `$ref` or matching fields. |
| **Primary Keys (Auto-inc/UUID)** | Document Object IDs (`_id`) | Document IDs are represented as primary identifier fields, not SQL primary keys. |
| **ACID Multi-Table Constraints** | Single-Document Atomicity | NoSQL collections will show "NO DECLARED CONSTRAINTS" unless rule-validated. |

---

## 4. Relationship Evidence Taxonomy

For future NoSQL dependency tracking, DERA defines a three-tier relationship evidence model:

1. **Declared Relationships**: Formally configured constraints in database engines (e.g., SQL Foreign Keys).
2. **Observed References**: Static analysis of application schemas or ORM definitions (e.g., Mongoose schemas, Prisma models).
3. **Derived Dependencies**: Inferred from historical query logs or data sample linkages.

Phase 7.5 displays **Declared Relationships exclusively**. Observed and Derived models will be activated in future milestones when verified analysis pipelines are in place.
