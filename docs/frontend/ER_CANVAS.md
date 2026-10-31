# Interactive ER Canvas Foundation

**Document Reference**: `docs/frontend/ER_CANVAS.md`  
**Milestone**: Phase 7.4 — Interactive ER Diagram Canvas & Relationship Visualization  

---

## 1. Canvas Viewport Engine

The ER Canvas is implemented as an interactive SVG surface managed by React state (`apps/web/src/components/er-diagram/ERCanvas.tsx`).

```xml
<svg className="w-full h-full block">
  <defs>
    <pattern id="er-grid" ... />
    <marker id="arrow-default" ... />
    <marker id="arrow-selected" ... />
    <marker id="arrow-highlighted" ... />
  </defs>
  <rect width="100%" height="100%" fill="url(#er-grid)" />
  <g transform={`translate(${viewport.x}, ${viewport.y}) scale(${viewport.zoom})`}>
    <g id="er-edges-layer">{/* RelationshipEdge components */}</g>
    <g id="er-nodes-layer">{/* TableNode components */}</g>
  </g>
</svg>
```

---

## 2. Layer Separation

1. **Background Grid Layer**: SVG dot matrix providing spatial reference during pan and zoom gestures.
2. **Edge Layer (`#er-edges-layer`)**: Rendered underneath table nodes so that connecting curves cleanly originate from and terminate at table card borders without crossing over table text.
3. **Node Layer (`#er-nodes-layer`)**: Rendered on top of edges for uninterrupted readability and selection.
4. **Interaction Layer**: Canvas-level mouse event handlers managing panning, wheel-based zooming toward cursor, and node dragging.

---

## 3. Viewport State & Transformations

```typescript
export interface ViewportState {
  x: number;     // Translation along horizontal axis (pixels)
  y: number;     // Translation along vertical axis (pixels)
  zoom: number;  // Scaling factor bounded between [0.2, 2.5]
}
```

- **Zoom to Cursor**: When mouse wheel moves, the canvas calculates the mouse offset relative to viewport translation and scales symmetrically toward the cursor coordinates.
- **Fit to View**: Bounding box calculations scan all visible node extents `[minX, minY, maxX, maxY]` and calculate optimal scale and centering offsets.
