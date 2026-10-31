# Maintainability Severity Model & Rationale

## Conservative Severity Policy

Maintainability diagnostics evaluate code organization, conventions, and engineering quality indicators. Unlike functional defects (such as missing primary keys or corrupt foreign key references), maintainability issues rarely cause immediate data corruption or system unavailability.

Therefore, Phase 8.4 enforces a conservative severity policy:
- **`CRITICAL`**: Strictly prohibited for maintainability findings.
- **`HIGH`**: Prohibited for maintainability findings (reserved for structural integrity defects in Phase 8.1–8.3).
- **`MEDIUM`**: Applied only when engine syntax execution is actively broken (e.g. unquoted reserved table name in `DERA-MNT-004`) or extreme complexity threatens schema migrations (e.g. large cyclic SCC $\ge 5$ tables in `DERA-MNT-007` or table width $\ge 100$ columns).
- **`LOW`**: Applied for elevated complexity thresholds (e.g., table width $\ge 50$ columns, structural coupling $\ge 12$, column nullability $\ge 75\%$, reserved column name).
- **`INFORMATIONAL`**: Applied for standard baseline thresholds (e.g., naming convention deviations, namespace imbalance, baseline wide tables $\ge 30$ columns, baseline nullability $\ge 50\%$).

## Severity Matrix

| Rule ID | Baseline Condition | Elevated Condition | Extreme Condition |
| :--- | :--- | :--- | :--- |
| `DERA-MNT-001` | $\ge 30$ cols (`INFORMATIONAL`) | $\ge 50$ cols (`LOW`) | $\ge 100$ cols (`MEDIUM`) |
| `DERA-MNT-002` | $\ge 50\%$ null (`INFORMATIONAL`)| $\ge 75\%$ null (`LOW`) | — |
| `DERA-MNT-003` | Naming deviation (`INFORMATIONAL`)| — | — |
| `DERA-MNT-004` | Reserved column (`LOW`) | Reserved table (`MEDIUM`) | — |
| `DERA-MNT-005` | Imbalance $\ge 90\%$ (`INFORMATIONAL`)| — | — |
| `DERA-MNT-006` | Degree $\ge 12$ (`LOW`) | Degree $\ge 24$ (`MEDIUM`) | — |
| `DERA-MNT-007` | SCC 3–4 tables (`LOW`) | SCC $\ge 5$ tables (`MEDIUM`) | — |
| `DERA-MNT-008` | $\ge 4$ LOBs (`INFORMATIONAL`) | $\ge 8$ LOBs (`LOW`) | — |
