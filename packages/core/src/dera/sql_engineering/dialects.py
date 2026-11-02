"""Explicit parser capabilities; MariaDB common syntax uses the MySQL grammar."""

PARSERS = {"postgresql": "postgres", "sqlite": "sqlite", "mysql": "mysql", "mariadb": "mysql"}


def resolve(dialect: str) -> str:
    if dialect not in PARSERS:
        raise ValueError("Unsupported SQL dialect")
    return PARSERS[dialect]
