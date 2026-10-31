# Findings Explorer Specification

## Functional Overview

The Findings Explorer provides an interactive, tabular interface for exploring schema findings across all rule categories.

## Table Structure and Columns

| Column | Information Displayed | Sorting Support |
| :--- | :--- | :--- |
| **Severity** | Discrete severity badge (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`, `INFORMATIONAL`) | Yes (by severity rank) |
| **Finding Title** | Human-readable title and single-line summary; suppression tag if exempted | No |
| **Rule ID** | Formal rule identifier (e.g. `DERA-CON-001`) | Yes (lexicographical) |
| **Affected Object** | Fully qualified canonical object identifier (e.g. `public.orders`) | Yes (lexicographical) |
| **Classification** | Discrete classification badge (e.g. `Structural Defect`, `Optimization Candidate`) | No |
| **Priority Rank** | Operational rank (`URGENT`, `IMPORTANT`, `NORMAL`, `LOW_PRIORITY`) | Yes (by priority score) |
| **Actions** | Eye icon button to inspect finding details | No |

## Pagination & Performance

- **Page Size**: Defaults to 10 findings per page, preserving snappy rendering on large reports.
- **Client Performance**: Virtualized and paged in-memory without blocking main thread responsiveness.
- **Keyboard Navigation**: Full `Tab` focus management with `Enter` and `Space` activation keys.
