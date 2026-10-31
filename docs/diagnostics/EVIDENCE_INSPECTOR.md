# Evidence Inspector Specification

## Overview

The Evidence Inspector displays strongly typed evidence items grounding each finding in verified canonical database objects.

## Evidence Card Structure

Each evidence entry presents:
- **Evidence Type**: Canonical object reference, column reference, index reference, constraint reference, graph edge, metric observation, or threshold comparison.
- **Completeness Badge**: Displays `Complete`, `Partial`, `Restricted`, or `Unsupported`.
- **Target Object**: Fully qualified entity name (`schema.table` or column).
- **Observed vs Expected**: Code-styled comparison of catalog findings against rule expectations.
- **Message**: Descriptive explanation of the anomaly.
- **Provenance**: Database engine name, connector version, and schema snapshot identity.
- **Deep Navigation**: Clickable link to inspect the object in the Table Inspector (`/app/tables?table=...`).
