# ER Table Node Rendering

**Document Reference**: `docs/frontend/ER_NODE_RENDERING.md`  
**Milestone**: Phase 7.4 — Interactive ER Diagram Canvas & Relationship Visualization  

---

## 1. Visual Specification

Table nodes are rendered as pure SVG cards (`apps/web/src/components/er-diagram/TableNode.tsx`) providing crisp scalability and zero dependency on HTML foreignObjects.

```text
+-----------------------------------------------------------+
| public                                           [6 cols] |
| customers                                                 |
+-----------------------------------------------------------+
| [PK]      id                                         uuid |
| [FK]      tenant_id                                  uuid |
|           name                               varchar(255) |
|           email                              varchar(255) |
|           created_at                          timestamptz |
+-----------------------------------------------------------+
|                     +2 more columns...                    |
+-----------------------------------------------------------+
```

---

## 2. Card Anatomy

1. **Card Frame**: Slate-900 background with rounded corners (`rx="8"`, `ry="8"`). Active border styling:
   - Default: `#334155` (1.5px stroke)
   - Highlighted: `#06b6d4` (2px cyan stroke)
   - Selected: `#3b82f6` (2.5px blue stroke with outer glow drop-shadow)
2. **Card Header**: 44px header bar displaying:
   - Namespace tag (uppercase monospace)
   - Table name (semibold typography, truncated if excessive length)
   - Column count badge
3. **Column Rows**: 22px height per row displaying:
   - Primary Key badge: Amber-600 background `[PK]`
   - Foreign Key badge: Blue-600 background `[FK]`
   - Column identifier: Monospace font, highlighted yellow if PK
   - Native data type: Right-aligned slate-500 monospace font
4. **Overflow Footer**: If a table has more than 8 columns, an overflow indicator `+N more columns...` indicates remaining fields.

---

## 3. Accessibility & Keyboard Control

Each table card declares:
- `role="button"`
- `tabIndex={0}`
- `aria-label="Table {namespace}.{name}, {N} columns"`
- Keyboard handler responding to `Enter` and `Space` to select the entity and open its details.
