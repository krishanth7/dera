# DERA Contributor Guide

**Project:** DERA — Database Engineering & Reverse Analysis  
**Policy Reference:** [CONTRIBUTING.md](../../CONTRIBUTING.md) · [CODE_OF_CONDUCT.md](../../CODE_OF_CONDUCT.md)  
**License:** [MIT License](../../LICENSE)

---

## 1. How to Contribute

We welcome contributions across multiple technical domains:
- **Database Connectors:** Expanding catalog extraction support for new engines (PostgreSQL, MySQL, SQLite, MariaDB, SQL Server).
- **Diagnostic Rules:** Writing deterministic rules to detect schema anti-patterns and performance bottlenecks.
- **Visual ER Studio:** Enhancing diagram layouts, export tools, and graph interaction performance.
- **Documentation & Localization:** Keeping documentation and translations accurate across all 10 supported languages.

---

## 2. Developing a New Database Connector

All database connectors must adhere to the base connector contract:

1. **Verify Supported Catalog Views:** Identify the official system catalog tables or views for the target database engine.
2. **Implement Read-Only Connection Guards:** Ensure the connection driver explicitly configures read-only transaction semantics.
3. **Map to Canonical Schema Model:** Normalize column types, constraints, and indexes into DERA's unified schema model.
4. **Handle Permission Errors Gracefully:** Provide actionable diagnostic feedback if a user's database role lacks permission to inspect specific schemas or objects.
5. **Add Integration Tests:** Include containerized integration tests validating schema discovery against synthetic test databases.

---

## 3. Contributing Documentation Translations

DERA supports 10 international languages in `docs/i18n/`. When submitting translation updates:
- Preserve all code blocks, command names, URLs, and file paths without translation.
- Maintain identical section structures and headings.
- Verify relative Markdown links.
- For Arabic documentation (`README.ar.md`), ensure that code snippets and diagrams remain in left-to-right formatting blocks.

---

## 4. Pull Request Checklist

Before submitting a pull request, ensure:
- [ ] Code strictly complies with the non-AI deterministic engineering philosophy.
- [ ] Automated tests have been added or updated.
- [ ] No database credentials, secrets, or `.env` files are included.
- [ ] Commit messages follow the [Conventional Commits](https://www.conventionalcommits.org/) specification.
- [ ] Documentation has been updated to reflect the changes.
