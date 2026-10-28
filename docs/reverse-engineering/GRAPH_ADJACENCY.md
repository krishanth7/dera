# Graph Adjacency Indexes & Queries

## 1. Adjacency Architecture

To achieve $O(1)$ relationship retrieval and avoid repeated full-graph scans, [`ForeignKeyGraph`](file:///packages/core/src/dera/reverse_engineering/graph/models.py) builds and caches an immutable [`AdjacencyIndex`](file:///packages/core/src/dera/reverse_engineering/graph/adjacency.py).

The index maintains pre-computed lookup tables:

- **Outgoing Adjacency**: Maps `source_table_id -> tuple[ForeignKeyEdge, ...]`.
- **Incoming Adjacency**: Maps `target_table_id -> tuple[ForeignKeyEdge, ...]`.
- **Pairwise Edge Index**: Maps `(source_table_id, target_table_id) -> tuple[ForeignKeyEdge, ...]`.
- **Outgoing Neighbor Index**: Maps `source_table_id -> tuple[ObjectId, ...]`.
- **Incoming Neighbor Index**: Maps `target_table_id -> tuple[ObjectId, ...]`.
- **All Neighbors Index**: Maps `table_id -> tuple[ObjectId, ...]`.

---

## 2. Query API

The root `ForeignKeyGraph` exposes high-level accessors that delegate directly to the index:

### 2.1. Outgoing Relationships
```python
edges: tuple[ForeignKeyEdge, ...] = graph.outgoing(table_id)
```
Returns all foreign key constraints declared by the table pointing to referenced parent tables.

### 2.2. Incoming Relationships
```python
edges: tuple[ForeignKeyEdge, ...] = graph.incoming(table_id)
```
Returns all foreign key constraints declared by other tables referencing this table as parent.

### 2.3. Direct Lookup Between Tables
```python
edges: tuple[ForeignKeyEdge, ...] = graph.relationships_between(source_table_id, target_table_id)
```
Returns all parallel foreign key edges directed from `source_table_id` to `target_table_id`.

### 2.4. Neighbor Queries
```python
# Outgoing neighbors (referenced parent tables)
parent_ids: tuple[ObjectId, ...] = graph.outgoing_neighbors(table_id)

# Incoming neighbors (referencing child tables)
child_ids: tuple[ObjectId, ...] = graph.incoming_neighbors(table_id)

# All adjacent neighbors (undirected union)
all_adjacent: tuple[ObjectId, ...] = graph.neighbors(table_id)
```

---

## 3. Algorithmic Complexity

| Method | Complexity | Notes |
| :--- | :--- | :--- |
| `outgoing(table_id)` | $O(1)$ | Direct dictionary lookup returning pre-built tuple. |
| `incoming(table_id)` | $O(1)$ | Direct dictionary lookup returning pre-built tuple. |
| `relationships_between(src, tgt)` | $O(1)$ | Direct dictionary lookup on `(src, tgt)` tuple key. |
| `outgoing_neighbors(table_id)` | $O(1)$ | Returns deduplicated, deterministically ordered tuple. |
| `incoming_neighbors(table_id)` | $O(1)$ | Returns deduplicated, deterministically ordered tuple. |
| `neighbors(table_id)` | $O(1)$ | Returns deduplicated, deterministically ordered tuple. |
