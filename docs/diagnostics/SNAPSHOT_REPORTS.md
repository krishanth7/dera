# Snapshot-Aware Reports Specification

## Overview

DERA Phase 8.6 supports evaluating and displaying diagnostics across immutable schema snapshots captured during Phase 6.

## Snapshot Integration Rules

1. **Explicit Identity**: The evaluation header clearly indicates whether the dashboard represents the `Live Schema` or an immutable `Snapshot (ID)`.
2. **No Data Mixing**: Findings from distinct snapshots are never combined without explicit labeling.
3. **Re-Evaluation Action**: Users can trigger an on-demand re-evaluation against the live database connection to detect newly fixed or introduced defects.
