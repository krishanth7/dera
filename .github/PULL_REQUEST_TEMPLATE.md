## Summary

<!-- Briefly describe the purpose, motivation, and context of this pull request. -->

## Change Type

<!-- Select all that apply: -->
- [ ] Feature (`feat`)
- [ ] Bug fix (`fix`)
- [ ] Documentation (`docs`)
- [ ] Refactor (`refactor`)
- [ ] Performance (`perf`)
- [ ] Test improvement (`test`)
- [ ] CI/CD or Build (`ci`, `build`)
- [ ] Security enhancement (`security`)
- [ ] Breaking change (`!`)

## Related Issues

<!-- Link relevant GitHub issues (e.g., Closes #12, Fixes #34). Leave empty if not applicable. -->
Closes #

## Implementation Details

<!-- Outline the technical approach, key files modified, or architectural decisions. -->
- 

## Testing Performed

<!-- Describe the verification steps taken. For documentation-only PRs, mention doc link checks. -->
- [ ] Unit tests executed (`python scripts/development/dev.py test` or `pytest`)
- [ ] Static type checks executed (`python scripts/development/dev.py typecheck`)
- [ ] Full baseline suite verified (`python scripts/development/dev.py all`)
- [ ] Integration tests against local test databases (if applicable)

## Security Impact & Deterministic Engineering

- [ ] **Strict Non-AI Policy:** Verified zero generative AI, LLM, or external inference APIs are introduced.
- [ ] **Database Safety:** Verified all database connector operations enforce read-only introspection without data modification.
- [ ] **Credential Protection:** Confirmed that no production credentials, passwords, or `.env` secrets are committed.
- [ ] **Least Privilege:** Validated that permissions and access boundaries are minimized.

## Documentation Impact

- [ ] Documentation in `docs/` updated or verified.
- [ ] Markdown link validation passed (`python scripts/ci/validate_docs.py`).
- [ ] No documentation updates required for this change.

## Breaking Changes

- [ ] No breaking changes.
- [ ] Breaking change introduced (detailed explanation and migration path below):

## Contributor Checklist

- [ ] My code adheres to the project's coding standards (PEP 8, TypeScript strict mode).
- [ ] My branch is rebased on the latest `main` branch.
- [ ] The PR title follows [Conventional Commits](https://www.conventionalcommits.org/) (e.g., `feat(connectors): add SQLite metadata support`).
- [ ] No unrelated changes or accidental files are included.
