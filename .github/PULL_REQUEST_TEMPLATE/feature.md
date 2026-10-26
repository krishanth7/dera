## Feature Summary

<!-- Describe the new capability, architectural enhancement, or algorithmic improvement. -->

## Motivation & Problem Solved

<!-- What database reverse-engineering challenge does this solve? Why is this necessary? -->

## Implementation Architecture

<!-- Outline the technical approach, key classes/modules modified, and design decisions. -->
- **Component Affected:** `packages/core` | `packages/connectors` | `packages/contracts` | `apps/api` | `apps/web`
- **Key Modules:** 
- **Deterministic Approach:** (Describe graph, catalog query, or AST algorithm used)

## Related Issue

Closes #

## Testing Performed

<!-- Detail test suites executed to verify functionality and prevent regressions. -->
- [ ] Unit tests added / updated (`python scripts/development/dev.py test`)
- [ ] Static typecheck passed (`python scripts/development/dev.py typecheck`)
- [ ] Full baseline suite verified (`python scripts/development/dev.py all`)
- [ ] Integration tests executed (if applicable)

## Architectural & Security Verification

- [ ] **Strict Non-AI Policy:** Confirmed 100% deterministic execution; zero AI/LLM runtime dependencies.
- [ ] **Database Safety:** Operations respect read-only constraints; zero customer table-row extraction.
- [ ] **Secret Protection:** Confirmed zero committed passwords, tokens, or private credentials.
- [ ] **Documentation:** Updated relevant documentation in `docs/` and added docstrings.
- [ ] **Conventional Commit Title:** PR title adheres to Conventional Commits (e.g., `feat(core): ...`).
