# Graph Edges Contract & Directionality

## 1. ForeignKeyEdge Model

Each directed edge in the graph represents a verified database foreign key constraint. Edges are implemented in [`ForeignKeyEdge`](file:///packages/core/src/dera/reverse_engineering/graph/edges.py):

```python
class ForeignKeyEdge(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    edge_id: ObjectId
    constraint_name: str
    source_table_id: ObjectId
    target_table_id: ObjectId
    column_pairs: tuple[ColumnPairMapping, ...]
    on_delete: ReferentialAction = ReferentialAction.NO_ACTION
    on_update: ReferentialAction = ReferentialAction.NO_ACTION
    match_type: MatchType = MatchType.NONE
    deferrability: ConstraintDeferrability = ConstraintDeferrability.NOT_DEFERRABLE
    is_enforced: bool = True
    is_self_referencing: bool = False
    source_namespace_name: str = ""
    target_namespace_name: str = ""
    provenance: MetadataProvenance | None = None
```

---

## 2. Canonical Direction Convention

DERA enforces a single canonical edge direction across the entire platform:

$$\text{Source FK Table (Child)} \longrightarrow \text{Referenced PK/UQ Table (Parent)}$$

### Rationale
In relational databases, the child table declares the constraint and holds the foreign key pointer referencing the parent table's primary or unique key.

### Example
```text
┌─────────────────────────┐               ┌─────────────────────────┐
│         orders          │               │        customers        │
│  (source_table_id)      ├──────────────►│   (target_table_id)     │
│                         │   order_fk    │                         │
│  customer_id (FK)       │               │  id (PK)                │
└─────────────────────────┘               └─────────────────────────┘
```

This directionality is invariant across all APIs, traversals, and serialization endpoints.

---

## 3. Parallel Edges (Multigraph Support)

When a table declares multiple foreign keys referencing the same parent table, each foreign key constraint is instantiated as a distinct edge.

### Example
```text
┌─────────────────────────┐               ┌─────────────────────────┐
│         orders          ├──created_by──►│          users          │
│                         │               │                         │
│                         ├──approved_by─►│                         │
└─────────────────────────┘               └─────────────────────────┘
```

- Edge 1: `fk_orders_created_by` (`orders.created_by -> users.id`)
- Edge 2: `fk_orders_approved_by` (`orders.approved_by -> users.id`)

Both edges share identical `source_table_id` and `target_table_id` but possess unique `edge_id`s and distinct column mappings.

---

## 4. Self-Referencing Edges (Self-Loops)

Tables with hierarchical structures reference themselves:

```text
┌─────────────────────────┐
│        employees        │◄──┐
│                         │   │ manager_id -> id
│                         ├───┘
└─────────────────────────┘
```

When `source_table_id == target_table_id`, the edge is flagged with `is_self_referencing = True`. Self-loops are handled gracefully during traversal, cycle detection, and connected components analysis without causing infinite recursion.

---

## 5. Deterministic Edge Ordering

Edges are sorted deterministically using [`sort_foreign_key_edges`](file:///packages/core/src/dera/reverse_engineering/graph/ordering.py):

$$\text{SortKey}(\text{edge}) = (\text{edge.source\_namespace\_name}, \text{edge.source\_table\_id}, \text{edge.constraint\_name}, \text{edge.edge\_id})$$
