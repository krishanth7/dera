# DERA-IDX-002: Potentially Redundant B-Tree Indexes (Leftmost Prefix Analysis)

## 1. Specification
Rule `DERA-IDX-002` identifies B-Tree indexes whose key terms are a strict leftmost prefix of a wider composite B-Tree index on the same table. For example, an index on `(customer_id)` may be covered by an index on `(customer_id, created_at)`.

## 2. Safety Constraints
- **B-Tree Only**: Prefix analysis is strictly prohibited for non-B-Tree methods (e.g. HASH, GIN, GiST, BRIN, FULLTEXT, SPATIAL).
- **Uniqueness Preservation**: A unique index on `(a)` cannot be replaced by a non-unique index on `(a, b)` because the wider index does not enforce uniqueness on `a`.
- **Predicate Equivalence**: Partial indexes must share identical WHERE predicates.
- **Sort & NULL Ordering**: Matching terms must share identical sort direction (ASC/DESC) and NULLS ordering.
- **Conservative Classification**: Findings are categorized as review candidates (`FindingClassification.POTENTIAL_OPTIMIZATION`) with `DiagnosticSeverity.LOW`, explicitly acknowledging that query workload, index sizes, and covering scans dictate runtime utility.
