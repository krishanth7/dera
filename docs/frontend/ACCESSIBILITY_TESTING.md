# Accessibility Automated & Manual Testing Procedures

**Module**: `apps/web/tests/`  
**Phase**: 7.6 — Accessibility, Responsive Design & Frontend Quality Assurance  

---

## 1. Testing Methodology

Accessibility verification in DERA combines automated rule checking with rigorous manual assistive technology evaluation:

1. **Automated Testing**: Programmatic verification of ARIA attributes, semantic roles, form error associations, and keyboard scroll regions in Vitest and React Testing Library.
2. **Manual Evaluation**: Human verification of focus rings, keyboard traps, screen reader audio output, and color independence.

---

## 2. Automated Test Coverage

In `apps/web/tests/component/accessibility_and_responsive.test.tsx`:
- **Skip Navigation**: Confirms `<a href="#main-content">` is present in DOM and points to focusable main landmark (`tabIndex="-1"`).
- **Form Error Association**: Confirms `Input` sets `aria-invalid="true"` when errors occur.
- **Button Loading States**: Confirms `Button` sets `aria-busy="true"` and disables element when `isLoading` is active.
- **Table Keyboard Region**: Confirms `Table` provides a keyboard-scrollable container with `role="region"` and `tabIndex="0"`.
- **Dialog Responsiveness**: Confirms `DialogContent` includes close button with `<span className="sr-only">Close</span>`.
- **Mobile Drawer Dismissal**: Confirms `Escape` key event listener closes the mobile navigation drawer.

---

## 3. Manual Testing Checklist

| Checklist Item | Requirement | Result |
| :--- | :--- | :--- |
| **Keyboard Only Operation** | Complete user journey from login to table inspection without pointer device | PASS |
| **Visible Focus Outlines** | Dual-contrast focus ring visible on all focusable elements in both themes | PASS |
| **No Keyboard Traps** | Tab navigation never becomes stuck inside a control or canvas | PASS |
| **Text Scaling (200%)** | Browser zoom at 200% reflows without overlapping or unreadable text | PASS |
| **Reduced Motion** | Disables canvas animations when `prefers-reduced-motion` is active | PASS |
| **High Contrast Mode** | Windows High Contrast / Forced Colors mode maintains clear borders | PASS |
