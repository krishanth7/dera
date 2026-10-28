# Composite Foreign Key Relationships

## 1. Overview

Relational databases permit foreign key constraints spanning multiple columns. A composite foreign key must preserve:

1. **Exact 1-to-1 Column Mapping**: Each source column maps to exactly one referenced column.
2. **Strict Sequence Ordering**: The ordinal sequence of column pairs must be identical to the database catalog declaration.
3. **Atomic Edge Representation**: A composite foreign key is represented as a single [`ForeignKeyEdge`](file:///packages/core/src/dera/reverse_engineering/graph/edges.py) containing multiple ordered [`ColumnPairMapping`](file:///packages/core/src/dera/reverse_engineering/graph/edges.py) objects. It is **never** split into separate single-column edges.

---

## 2. ColumnPairMapping Model

The atomic column association is defined in [`ColumnPairMapping`](file:///packages/core/src/dera/reverse_engineering/graph/edges.py):

```python
class ColumnPairMapping(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    source_column: str
    target_column: str
    ordinal_position: int = 0
```

---

## 3. Structural Representation

Consider an order item relationship referencing a partitioned or multi-tenant order header:

```sql
ALTER TABLE order_items
  ADD CONSTRAINT fk_order_items_orders
  FOREIGN KEY (tenant_id, order_id)
  REFERENCES orders (tenant_id, id);
```

### Graph Representation:

```text
Edge:
  edge_id: "obj_fk_order_items_orders_123"
  source_table_id: "obj_table_order_items_abc"
  target_table_id: "obj_table_orders_xyz"
  column_pairs:
    [0] ColumnPairMapping(source_column="tenant_id", target_column="tenant_id", ordinal_position=0)
    [1] ColumnPairMapping(source_column="order_id",  target_column="id",        ordinal_position=1)
```

---

## 4. Validation & Error Handling

During graph construction, the [`ForeignKeyGraphBuilder`](file:///packages/core/src/dera/reverse_engineering/graph/builder.py) validates composite keys against the following rules:

1. **Length Parity**: The number of source columns must match the number of target columns. A mismatch triggers a `GraphValidationError` (or `UnresolvedReference` depending on validation mode).
2. **Non-Empty Mappings**: A foreign key must specify at least one column pair. Empty mappings are rejected.
3. **Column Existence**: When source table columns are known, source column existence is verified.
4. **Sequence Determinism**: Column pairs are sorted by `ordinal_position` using [`sort_column_pairs`](file:///packages/core/src/dera/reverse_engineering/graph/ordering.py).
