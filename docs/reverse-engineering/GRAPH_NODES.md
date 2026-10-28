# Graph Nodes Contract & Architecture

## 1. TableNode Model

A graph node represents a verified physical or logical database table. Nodes are implemented in [`TableNode`](file:///packages/core/src/dera/reverse_engineering/graph/nodes.py):

```python
class TableNode(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    table_id: ObjectId
    namespace_id: ObjectId
    table_name: str
    namespace_name: str
    table_type: TableClassification = TableClassification.BASE_TABLE
    column_count: int = 0
    primary_key_columns: tuple[str, ...] = Field(default_factory=tuple)
    is_view: bool = False
    completeness: MetadataCompleteness = MetadataCompleteness.COMPLETE
    provenance: MetadataProvenance | None = None
```

---

## 2. Node Identity & Stability

Node identities are strictly inherited from Phase 5.5 canonical `ObjectId`s:

1. **Deterministic Hashing**: Formatted via `LengthPrefixedSHA256(workspace_id, object_kind, qualifier, name)`.
2. **Workspace Isolation**: Preserves workspace boundaries and prevents collision across workspaces or databases.
3. **Immutable Stability**: Node `table_id` is invariant under serialization, deserialization, and schema re-inspection.
4. **No Inferred Nodes**: Nodes are only constructed for tables that exist in the canonical schema. If a foreign key points to a missing table, an `UnresolvedReference` is recorded; no synthetic table node is created.

---

## 3. Node Classifications

The `table_type` attribute leverages the canonical [`TableClassification`](file:///packages/core/src/dera/metadata/enums.py) enum:

- `BASE_TABLE`: Standard relational table holding row data.
- `VIEW`: Standard database view.
- `MATERIALIZED_VIEW`: Database view with persisted physical storage.
- `TEMPORARY_TABLE`: Session-scoped or transaction-scoped temporary table.
- `FOREIGN_TABLE`: External table mapped via SQL/MED or FDW.
- `PARTITIONED_TABLE`: Partitioned parent or child table.

---

## 4. Deterministic Ordering

To ensure consistent outputs regardless of input collection order, nodes are deterministically ordered using the following key in [`sort_table_nodes`](file:///packages/core/src/dera/reverse_engineering/graph/ordering.py):

$$\text{SortKey}(\text{node}) = (\text{node.namespace\_name}, \text{node.table\_name}, \text{node.table\_id})$$
