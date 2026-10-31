# DERA-REL-004: Cross-Namespace Dependency Structure

## 1. Rule Definition
- **Rule ID**: `DERA-REL-004`
- **Rule Title**: Cross-Namespace Dependency Structure
- **Category**: `RELATIONSHIPS`
- **Default Severity**: `INFORMATIONAL`
- **Applicability**: Relational engines with multiple schemas/namespaces (PostgreSQL, Supabase PostgreSQL, MySQL, MariaDB).

## 2. Architectural Context
In modular architectures and micro-service backends, schemas often delineate bounded contexts (e.g. `auth`, `billing`, `analytics`). Foreign keys spanning schemas create cross-boundary coupling:
- Cross-schema relationships couple lifecycle and deployment cadence across schemas.
- Backup, restore, and selective migration across namespaces require topological coordination.
- Granular database permissions across schemas must be maintained.

## 3. Severity & Policy
Cross-namespace foreign keys are valid relational constructs, not bugs. Therefore:
- Severity is strictly `INFORMATIONAL`.
- Findings provide clear architectural visibility for domain-driven design, schema modularization, and service decomposition planning.
