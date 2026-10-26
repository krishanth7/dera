## Bugfix Summary

<!-- Concisely explain what was broken, what caused the failure, and how this fix resolves it. -->

## Root Cause Analysis

<!-- What specific defect in logic, parsing, or edge cases caused the unexpected behavior? -->

## Related Issue

Fixes #

## Solution & Code Changes

<!-- Outline the minimal surgical fix applied. -->
- **Component:** 
- **Files Modified:** 
- **Side Effect Assessment:** 

## Regression Testing Verification

<!-- Bug fixes must include automated regression tests preventing recurrence. -->
- [ ] Added automated regression test under `tests/regression/` reproducing the original defect.
- [ ] All unit and integration tests passing (`python scripts/development/dev.py test`).
- [ ] Static typecheck clean (`python scripts/development/dev.py typecheck`).
- [ ] Full baseline suite verified (`python scripts/development/dev.py all`).

## Security & Quality Checklist

- [ ] Verified fix does not loosen security boundaries or read-only guarantees.
- [ ] Verified fix does not introduce non-deterministic or third-party AI dependencies.
- [ ] Sanitized error handling: no connection secrets or internal paths leaked to users.
- [ ] PR title follows Conventional Commits: `fix(<scope>): <description>`.
