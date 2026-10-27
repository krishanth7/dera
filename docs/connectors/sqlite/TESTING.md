# DERA SQLite Connector Testing Strategy

## Overview

The SQLite connector test suite validates functionality across unit, conformance, filesystem security, and live integration boundaries.

---

## Test Organization

```text
tests/
├── connectors/sqlite/
│   ├── test_configuration.py         # Validation of configuration models & bounds
│   ├── test_filesystem_security.py   # Path traversal, null byte, and root guards
│   ├── test_errors.py                # Error mapping, taxonomy, & path redaction
│   ├── test_type_affinity.py         # SQLite 3 type affinity rules 1-5 verification
│   ├── test_catalog_queries.py       # PRAGMA builders & DDL check parsing
│   └── test_sqlite_adapter.py        # BaseConnectorConformanceTests conformance suite
└── integration/sqlite/
    └── test_sqlite_live.py           # End-to-end integration, WAL mode, & read-only lock
```

---

## Running the Tests

Execute all SQLite test suites via Python `unittest`:

```bash
# Unit & conformance tests
python -m unittest discover -s tests/connectors/sqlite -p "test_*.py"

# Live integration & read-only security tests
python -m unittest discover -s tests/integration/sqlite -p "test_*.py"

# Complete connector suite
python -m unittest discover -s tests/ -p "test_*.py"
```
