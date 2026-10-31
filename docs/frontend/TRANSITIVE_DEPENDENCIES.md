# Transitive Dependency Exploration & Reachability

**Module**: `apps/web/src/components/dependency-explorer/TransitiveReachabilityPanel.tsx`  
**Route**: `/dependencies` & `/dependencies/[objectId]`  
**Phase**: 7.5 — Table Inspector, Advanced Search & Dependency Visualization  

---

## 1. Overview

Transitive dependency exploration allows database engineers to trace multi-hop relationship chains beyond immediate foreign key links. In DERA, dependency traversal is deterministic and bounded, preventing infinite loops or UI hangs in cyclic schemas.

```text
+-------------------------------------------------------------------------+
|                  Transitive Dependency Reachability                     |
+-------------------------------------------------------------------------+
| Focus Table: [ orders                                                 ] |
| Depth: ( ) Direct (1)   ( ) 2-Hop   ( ) 3-Hop   (*) Full Transitive     |
+------------------------------------+------------------------------------+
| Upstream Prerequisites             | Downstream Blast Radius            |
| (Tables orders depends upon)       | (Tables that depend upon orders)   |
+------------------------------------+------------------------------------+
| * users (depth: 1)                 | * order_items (depth: 1)           |
| * organization (depth: 2 via users)| * shipments (depth: 2 via items)   |
| * tenant (depth: 3 via org)        | * invoices (depth: 2 via orders)   |
+------------------------------------+------------------------------------+
```

---

## 2. Directional Traversal Semantics

Traversals adhere to Phase 6.3 and Phase 6.4 graph orientation invariants:

1. **Foreign Key Edge Direction**: An edge $E = (u \to v)$ indicates that table $u$ contains a foreign key referencing table $v$.
2. **Upstream Traversal (Prerequisites)**:
   - Traverses edges in forward direction ($u \to v$).
   - Identifies tables that must exist before the focal table can be created or populated.
3. **Downstream Traversal (Blast Radius / Dependents)**:
   - Traverses edges in reverse direction ($v \leftarrow u$).
   - Identifies tables that rely on the focal table, representing objects impacted by drops, truncates, or schema mutations.

---

## 3. Bounded Reachability Algorithm

The client-side reachability engine executes a bounded Breadth-First Search (BFS):

```typescript
function computeReachability(
  focalTableId: string,
  adjacencyList: Map<string, string[]>,
  maxDepth: number
): Map<string, number> {
  const visited = new Map<string, number>();
  const queue: Array<{ id: string; depth: number }> = [{ id: focalTableId, depth: 0 }];

  while (queue.length > 0) {
    const { id, depth } = queue.shift()!;
    if (depth >= maxDepth) continue;

    const neighbors = adjacencyList.get(id) || [];
    for (const neighbor of neighbors) {
      if (!visited.has(neighbor) && neighbor !== focalTableId) {
        visited.set(neighbor, depth + 1);
        queue.push({ id: neighbor, depth: depth + 1 });
      }
    }
  }

  return visited;
}
```

### Depth Limits

- **`1` (Direct)**: Immediate foreign key neighbors only.
- **`2` (Two-Hop)**: Immediate neighbors plus their immediate neighbors.
- **`3` (Three-Hop)**: Up to three edge traversals.
- **`transitive` (Full)**: Exhaustive traversal bounded by graph diameter or hard-capped at 20 hops to prevent CPU starvation.

---

## 4. UI Presentation & Navigation

- **Depth Selector**: Radio pills allowing instantaneous recalculation without backend roundtrips when the full dependency graph is in memory.
- **Hop Badges**: Visual indicators (`depth: 1`, `depth: 2`, `depth: 3+`) highlighting proximity to the focal table.
- **Direct Navigation**: Clicking any listed table sets it as the new focal table, dynamically repopulating upstream and downstream trees.
