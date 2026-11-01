# Schema Change Classification & Compatibility Model

**Phase:** 9.2 — Schema Change Classification & Migration Risk Analysis  

---

## 1. Structural Change Categories

Every schema change is classified into one of 8 categories:
- `ADDITIVE`: Addition of tables, columns, constraints, or namespaces.
- `REMOVAL`: Removal of existing schema objects.
- `MODIFICATION`: Changes to object metadata or column properties.
- `CONSTRAINT_CHANGE`: Modifications to PK, FK, unique, or check constraints.
- `INDEX_CHANGE`: Additions, removals, or property alterations to indexes.
- `RELATIONSHIP_CHANGE`: Directed relationship multigraph edge adjustments.
- `NAMESPACE_CHANGE`: Schema/namespace alterations.
- `DEFINITION_CHANGE`: View SQL query definition updates.

## 2. Compatibility Levels

- `COMPATIBLE_WITH_KNOWN_METADATA`: Safe additive changes (e.g. adding a nullable column).
- `POTENTIALLY_BREAKING`: Dropping objects or narrowing column data types.
- `BREAKING_UNDER_STATED_CONDITIONS`: Enforcing NOT NULL or new constraints on populated tables.
- `REQUIRES_REVIEW`: Workload-dependent changes such as dropping an index or altering view SQL.
- `INDETERMINATE`: Metadata completeness prevents definitive classification.
- `UNSUPPORTED`: Unsupported dialect features.
