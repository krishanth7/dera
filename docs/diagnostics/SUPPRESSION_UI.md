# Suppression User Interface Specification

## Overview

The Suppression UI provides auditable, authorized exemption management. Findings are never silently hidden; exemptions are time-bounded and logged.

## User Workflow

1. **Applying an Exemption**: An authorized engineer clicks **Exempt Finding**, provides a mandatory justification reason, and selects an expiration duration (7 days, 30 days, 90 days, 1 year).
2. **Reviewing Exemption State**: Suppressed findings display a `Suppressed` pill in the table and retain full visibility when filtering by `Suppressed Only`.
3. **Revocation**: Clicking **Revoke Exemption** immediately restores the finding to active status.
