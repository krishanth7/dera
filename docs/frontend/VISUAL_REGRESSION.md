# Visual Regression & Cross-Theme Verification

**Module**: `apps/web/`  
**Phase**: 7.6 — Accessibility, Responsive Design & Frontend Quality Assurance  

---

## 1. Visual Verification Goals

Visual regression testing guarantees that style refactorings, theme switches, and layout changes do not inadvertently introduce:

- Pixel-level layout shifting (CLS > 0.1).
- Unintended text wrapping or overlapping badges.
- Inconsistent border colors between light and dark themes.
- Clipped dialog content or hidden action buttons on mobile screens.

---

## 2. Tested Visual States & Snapshots

Visual test coverage includes the following critical studio states:

1. **Light Theme Baseline**:
   - Corporate Slate/Indigo palette (`#2563EB` primary, `#0F172A` text on `#F8FAFC`).
   - Clean tabular lines, subtle cards, and high-contrast badges.
2. **Dark Theme Baseline**:
   - High-contrast technical dark palette (`#3B82F6` primary on `#0F172A` dark background).
   - Inverted borders (`#334155`) with guaranteed 4.5:1 text contrast.
3. **Responsive Mobile Views (375px)**:
   - Header with hamburger trigger, breadcrumb collapse, stacked cards.
   - Mobile navigation drawer open overlay state.
4. **Interactive Studio Views**:
   - Table Inspector with active Columns tab and expanded column detail drawer.
   - Advanced Search with active filter pills and paginated result items.
   - Dependency Explorer with cycle alert banner and parallel execution ordering.
   - ER Canvas with table node selection and relationship details drawer open.
