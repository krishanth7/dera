# Severity Visualization Specification

## Visualization Strategy

DERA avoids communicating severity through color alone, ensuring compliance with WCAG 2.2 Level AA guidelines.

## Multi-Modal Visual Presentation

1. **Color Coded Bars & Badges**:
   - `CRITICAL`: Red `#dc2626`
   - `HIGH`: Amber `#d97706`
   - `MEDIUM`: Yellow `#eab308`
   - `LOW`: Blue `#2563eb`
   - `INFORMATIONAL`: Slate `#64748b`
2. **Textual Labels**: Every visual element includes explicit text denoting the level (e.g., `Critical Defect`, `High Priority`).
3. **Screen-Reader Data Tables**: For visually impaired users utilizing assistive technology, each visual chart is accompanied by a hidden HTML data table containing exact numerical counts and percentages.
4. **Interactive Filters**: Clicking any severity card updates the active filter state, instantly narrowing the findings table.
