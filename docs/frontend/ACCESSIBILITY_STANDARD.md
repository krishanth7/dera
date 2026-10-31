# Accessibility Standards & WCAG 2.2 AA Compliance

**Module**: `apps/web/`  
**Phase**: 7.6 — Accessibility, Responsive Design & Frontend Quality Assurance  

---

## 1. Objective & Target Specification

DERA enforces the Web Content Accessibility Guidelines (WCAG) 2.2 Level AA standard across the entire frontend application. Accessibility is treated as a fundamental architectural pillar rather than an optional cosmetic layer, ensuring database reverse engineering and schema inspection are completely usable by engineers relying on assistive technologies or keyboard-only input.

```text
+--------------------------------------------------------------------------+
|                     DERA Accessibility Architecture                      |
+--------------------------------------------------------------------------+
|  Semantic HTML5       | Native landmarks: <main>, <nav>, <header>        |
|  ARIA Specifications  | Explicit roles, live regions, aria-describedby   |
|  Visual Invariants    | Minimum 4.5:1 text & 3:1 graphical element ratio |
|  Motor Invariants     | Complete keyboard operation, visible focus rings |
|  Assistive Tech       | Accessible tabular alternatives for all graphs   |
+--------------------------------------------------------------------------+
```

---

## 2. WCAG 2.2 Level AA Conformance Matrix

| Principle | Guideline / Success Criterion | Implementation in DERA |
| :--- | :--- | :--- |
| **Perceivable** | **1.1.1 Non-text Content** | All icons and graphical elements feature descriptive `aria-label` or `aria-hidden="true"`. |
| | **1.3.1 Info and Relationships** | Strict HTML5 semantic hierarchy; tables use `<th>`, `<caption>`, and `scope`. |
| | **1.4.1 Use of Color** | Status indicators (`COMPLETE`, `PARTIAL`, `RESTRICTED`) combine color, badges, text, and icons. |
| | **1.4.3 Contrast (Minimum)** | Primary text >= 7:1; secondary text >= 4.5:1; borders and focus rings >= 3:1. |
| | **1.4.10 Reflow** | Clean single-column adaptation down to 320px viewport without clipping or data loss. |
| | **1.4.11 Non-text Contrast** | Interactive buttons, inputs, and diagram node borders exceed 3:1 ratio. |
| **Operable** | **2.1.1 Keyboard** | 100% of workflows (connections, explorer, inspector, canvas) operable via keyboard. |
| | **2.1.2 No Keyboard Trap** | Focus is safely managed; modals and drawers release focus on `Escape` or tab-out. |
| | **2.4.1 Bypass Blocks** | Skip-to-content navigation link (`#main-content`) accessible as the first focusable element. |
| | **2.4.7 Focus Visible** | High-visibility dual-contrast focus outlines across light and dark modes. |
| | **2.5.8 Target Size (Minimum)** | Interactive touch targets meet or exceed 24x24px (standard inputs/buttons >= 36px). |
| **Understandable** | **3.2.1 On Focus** | Focus change never automatically submits forms or modifies workspace state. |
| | **3.3.1 Error Identification** | Form inputs mark invalid fields with `aria-invalid="true"` and descriptive text. |
| | **3.3.2 Labels or Instructions** | Programmatic labels provided for all inputs, selectors, and search fields. |
| **Robust** | **4.1.2 Name, Role, Value** | Proper ARIA roles (`dialog`, `region`, `tablist`, `tab`, `tabpanel`) with state sync. |
| | **4.1.3 Status Messages** | Asynchronous operations announce status via ARIA live regions and toasts. |
