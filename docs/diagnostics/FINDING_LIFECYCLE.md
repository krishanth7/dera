# Finding Lifecycle Specification

## Overview

In enterprise database engineering workflows, findings are tracked across time through a formalized lifecycle state machine. DERA Phase 8.5 specifies states, permitted transitions, and strict safety rules governing when findings may change status.

## Lifecycle States

| State | Definition | Description |
| :--- | :--- | :--- |
| `OPEN` | Active, unaddressed finding | Default state upon discovery in an evaluation |
| `ACKNOWLEDGED` | Reviewed by engineering | Acknowledged as a known issue, pending work scheduling |
| `SUPPRESSED` | Formally exempted | Suppressed by authorized governance policy with documented reason |
| `RESOLVED` | Defect eliminated in schema | Object verified as fixed or removed in subsequent snapshot |
| `REOPENED` | Regression detected | Previously resolved defect reappeared in a recent snapshot |

## Lifecycle Transition Matrix

```text
[OPEN] ------------> [ACKNOWLEDGED]
  |                         |
  +--------> [SUPPRESSED] <-+
  |               |
  v               v
[RESOLVED] <------+
  |
  +-----------------> [REOPENED]
```

## Lifecycle Safety Invariants

1. **No Automatic Resolution on Missing Snapshots**: A finding is marked `RESOLVED` only if the schema object was evaluated in a new snapshot and verified to no longer violate the rule. A failed, skipped, or truncated evaluation must **never** auto-resolve open findings.
2. **Audit Preservation**: State transitions record the actor, timestamp, prior state, new state, and reason in an append-only audit trail.
