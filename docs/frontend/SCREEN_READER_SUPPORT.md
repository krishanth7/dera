# Screen-Reader Support & Assistive Technology Matrix

**Module**: `apps/web/`  
**Phase**: 7.6 — Accessibility, Responsive Design & Frontend Quality Assurance  

---

## 1. Overview

Engineers using screen readers (NVDA, JAWS, VoiceOver, Orca) must be able to explore complex database relationships, constraints, indexes, and cycles with full semantic context. DERA avoids relying on spatial or visual geometry by providing complete textual and tabular alternatives.

```text
+--------------------------------------------------------------------------+
|                  Visual Graph & Spatial Canvas Mode                      |
|                  (Interactive SVG with coordinates)                      |
+------------------------------------+-------------------------------------+
                                     |
                          [ Accessible Mode Toggle ]
                                     |
                                     v
+--------------------------------------------------------------------------+
|               Accessible Semantic HTML Data Table Mode                   |
|  - Table Name & Namespace in <caption> and <th scope="row">             |
|  - Inbound & Outbound Relationships in <th scope="col">                  |
|  - Topological Level & Cycle Membership announced explicitly             |
+--------------------------------------------------------------------------+
```

---

## 2. Screen Reader Testing Matrix

The following combinations represent verified testing targets:

| Operating System | Screen Reader | Primary Browser | Status | Verification Focus |
| :--- | :--- | :--- | :--- | :--- |
| **Windows 11** | NVDA (Latest) | Google Chrome | Supported | Skip link, ARIA tabs, form error announcements |
| **Windows 11** | NVDA (Latest) | Mozilla Firefox | Supported | Data table headers, keyboard navigation, dialogs |
| **macOS Sequoia** | VoiceOver | Apple Safari | Supported | Visual canvas alternative table, live regions |
| **Linux (Ubuntu)** | Orca | Mozilla Firefox | Supported | Core navigation landmarks, connection wizard |
| **iOS / iPadOS** | VoiceOver | Mobile Safari | Supported | Mobile navigation drawer, responsive forms |

---

## 3. ARIA Live Regions & Dynamic Notifications

- **Toast System (`ToastProvider`)**: Status messages (success, warning, error) use `role="status"` and `aria-live="polite"` so screen readers speak notifications without interrupting user speech.
- **Search Result Counters**: Dynamically populated search result counts announce `"[N] matching objects found"` upon query completion.
- **Connection Test Feedback**: Engine probe states announce `"Connection probe in progress..."` followed by `"Connection successful"` or `"Connection failed: [reason]"`.
