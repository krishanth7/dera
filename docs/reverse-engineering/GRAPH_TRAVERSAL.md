# Graph Traversal & Connected Components

## 1. Traversal Engine Overview

Graph traversal in DERA is strictly deterministic and bounded. The engine in [`traversal.py`](file:///packages/core/src/dera/reverse_engineering/graph/traversal.py) provides:

- **Breadth-First Search (BFS)**
- **Depth-First Search (DFS)**
- **Weakly Connected Components (WCC)**

Unbounded recursive operations are prohibited. All traversals enforce limits on maximum depth, maximum visited nodes, and maximum returned edges.

---

## 2. Traversal Directions

Traversals can follow three directional modes via [`TraversalDirection`](file:///packages/core/src/dera/reverse_engineering/graph/traversal.py):

1. **`OUTGOING`**: Follows edges along canonical direction (`Child FK -> Parent PK`). Useful for determining prerequisite tables that must be created before the current table.
2. **`INCOMING`**: Follows edges in reverse direction (`Parent PK <- Child FK`). Useful for impact analysis (which tables depend on this parent table).
3. **`BOTH` / `UNDIRECTED`**: Explores edges in either direction.

---

## 3. Bounded Traversal Execution

Traversals accept explicit limit overrides or inherit from [`GraphResourceLimits`](file:///packages/core/src/dera/reverse_engineering/graph/limits.py):

```python
result = graph.traverse(
    start_table_id=orders_id,
    direction=TraversalDirection.OUTGOING,
    algorithm="bfs",
    max_depth=5,
    max_visited_nodes=100,
    max_returned_edges=200,
    raise_on_limit=False,  # Truncates gracefully if True/False
)
```

### TraversalResult Structure
```python
class TraversalResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    start_table_id: ObjectId
    visited_table_ids: tuple[ObjectId, ...]
    traversed_edges: tuple[ForeignKeyEdge, ...]
    depth_reached: int
    truncated: bool = False
    truncation_reason: str | None = None
```

When limits are reached:
- If `raise_on_limit=True`, raises [`TraversalLimitExceededError`](file:///packages/core/src/dera/reverse_engineering/graph/errors.py).
- If `raise_on_limit=False`, terminates traversal cleanly, setting `truncated=True` and populating `truncation_reason`.

---

## 4. Weakly Connected Components (WCC)

The method `find_weakly_connected_components(graph)` identifies disjoint subgraphs.

### Semantics
- Treats directed foreign key edges as undirected for connectivity partitioning.
- Isolated tables with zero foreign keys appear as single-node components.
- Deterministically sorts components:
  1. Component table count descending (largest clusters first).
  2. Lexicographical comparison of lowest `table_id` in each component for ties.
- Tables within each component are sorted deterministically.
