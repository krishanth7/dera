## Summary

<!-- Briefly describe the purpose and context of this change. -->

## Related Issue

<!-- Link the relevant issue (e.g., Closes #12, Fixes #34). -->
Closes #

## Changes Made

<!-- Bullet points summarizing the technical changes. -->
- 
- 
- 

## Deterministic Engineering & Non-AI Verification

- [ ] This change is completely deterministic and introduces **no** generative AI models, LLMs, or external inference APIs.

## Testing Performed

<!-- Detail the test strategy: unit tests, integration tests, or manual validation. -->
- [ ] Added or updated unit tests (`pytest tests/unit`)
- [ ] Added or updated integration tests against test databases
- [ ] Verified that CodeQL analysis and documentation checks pass

## Security Considerations

<!-- Address any security implications: database connection permissions, credential handling, or SSRF risks. -->
- [ ] Confirmed that no production credentials, database passwords, or `.env` secrets are committed.
- [ ] Confirmed that database operations enforce read-only semantics.

## Breaking Changes

<!-- Does this PR introduce breaking changes to schema models, APIs, or database connector behavior? -->
- [ ] No breaking changes
- [ ] Breaking changes (described below):

## Contributor Checklist

- [ ] My code adheres to the project's coding standards and PEP 8 / TypeScript conventions.
- [ ] Documentation in `docs/` and localized READMEs have been updated where applicable.
- [ ] Commit messages follow the [Conventional Commits](https://www.conventionalcommits.org/) specification.
