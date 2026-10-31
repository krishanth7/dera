# Composite Foreign Keys Visualization

**Document Reference**: `docs/frontend/ER_COMPOSITE_KEYS.md`  
**Milestone**: Phase 7.4 — Interactive ER Diagram Canvas & Relationship Visualization  

---

## 1. Principles of Composite Relationships

A composite foreign key constraint binds multiple columns in a referencing table to matching columns in a referenced table. DERA treats every composite foreign key as a **single, unified relationship edge** rather than splitting it into independent visual lines.

```text
orders(tenant_id, customer_id)
      │          │
      ▼          ▼
customers(tenant_id, id)
```

---

## 2. Ordered Pair Mapping

In `apps/web/src/components/er-diagram/layout.ts`, composite edges are decomposed into ordered pairs preserving the exact ordinal correspondence:

```typescript
const column_pairs: ColumnPairMapping[] = [];
for (let i = 0; i < len; i++) {
  column_pairs.push({
    source_column: edge.source_columns[i],
    target_column: edge.target_columns[i],
  });
}
```

---

## 3. Visual Representation

1. **Canvas Path**: Dashed stroke line (`strokeDasharray="5,3"`) with an embedded pill badge `[N cols]` anchored at the curve midpoint.
2. **Details Drawer**: The `RelationshipDetails` panel displays an explicit mapping table:
   - Child column
   - Direction arrow `→`
   - Parent column
3. **Accessibility**: Screen reader labels read:
   `"Composite Foreign key {name} from {child} to {parent} ({N} columns)"`
