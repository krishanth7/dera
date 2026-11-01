# Diagnostics Dashboard Accessibility Specification

## WCAG 2.2 Level AA Compliance

The Diagnostics Dashboard adheres to the WCAG 2.2 Level AA accessibility standards.

## Accessibility Verification Matrix

| WCAG Criterion | Implementation Detail |
| :--- | :--- |
| **1.1.1 Non-text Content** | All icons (e.g. `ShieldAlert`, `CheckCircle2`) include `aria-hidden="true"` and companion textual labels. |
| **1.3.1 Info and Relationships** | Native HTML semantic landmarks (`<aside>`, `<table scope="col">`, `<header>`) and ARIA roles. |
| **1.4.1 Use of Color** | Severity is never communicated through color alone. Every badge has explicit text and icons. |
| **1.4.3 Contrast (Minimum)** | Text meets or exceeds 4.5:1 contrast ratios in light and dark modes. |
| **2.1.1 Keyboard Accessible** | Every interactive element, filter button, and table row is operable via `Tab`, `Enter`, and `Space`. |
| **2.4.7 Focus Visible** | Distinct focus ring rings (`focus:ring-2 focus:ring-blue-500`) on all interactive controls. |
| **4.1.2 Name, Role, Value** | Custom dialogs, buttons, and progress indicators have descriptive ARIA names and live status values. |
