# Explorer Performance Specification

**Document Reference**: `docs/frontend/EXPLORER_PERFORMANCE.md`  
**Milestone**: Phase 7.3 — Database Connection & Schema Explorer UI  

---

## 1. Large Schema Optimization Strategies

Enterprise databases frequently contain hundreds of tables and thousands of columns. DERA employs multi-tier performance optimizations to guarantee fluid interaction.

### Performance Controls

1. **Lazy Table Detail Loading**: The schema catalog and navigation tree load compact table summary objects (`TableSummaryItem`). Exhaustive column and constraint definitions (`TableDetailItem`) are fetched on-demand upon node selection.
2. **Component Memoization**: Pure React components (`useMemo`) isolate navigation tree updates from detail studio tab switches.
3. **Optimized Virtual DOM Updates**: Radix UI tabs and dialogs mount and unmount child viewports dynamically to minimize active DOM node counts.
4. **Debounced Search**: Text search operates on local in-memory indexes with debounced event handlers to avoid unnecessary render loops.
5. **Static Bundle Splitting**: Next.js route splitting isolates the Schema Explorer code bundle from unauthenticated marketing and connection setup bundles.
