# Cross-Browser Support & Compatibility Matrix

**Module**: `apps/web/`  
**Phase**: 7.6 — Accessibility, Responsive Design & Frontend Quality Assurance  

---

## 1. Supported Browser Tiers

DERA supports evergreen desktop and mobile browsers adhering to ECMAScript 2022+ standards:

| Browser | Supported Minimum Version | Engine | Testing Status |
| :--- | :--- | :--- | :--- |
| **Google Chrome** | 120+ | Blink / V8 | Primary Target (Pass) |
| **Microsoft Edge** | 120+ | Blink / V8 | Supported (Pass) |
| **Mozilla Firefox** | 120+ | Gecko / SpiderMonkey | Supported (Pass) |
| **Apple Safari** | 17+ | WebKit / JavaScriptCore | Supported (Pass) |
| **Mobile Chrome (Android)** | Current stable | Blink | Supported (Pass) |
| **Mobile Safari (iOS)** | 17+ | WebKit | Supported (Pass) |

---

## 2. Platform Feature Compatibility

- **CSS Nesting & Color Schemes**: Native CSS variables with HSL color tuples supported uniformly across Blink, Gecko, and WebKit.
- **SVG Transform Matrices**: ER Canvas panning and scaling transforms tested for sub-pixel rendering accuracy without canvas blur across Safari and Chrome.
- **Scroll Snap & Regions**: Smooth scroll regions for data tables verified on Firefox and Safari without layout shifting.
- **Radix UI Primitives**: Standard accessible dialogs, portals, and dropdowns exhibit identical ARIA behavior on all tier-1 browsers.
