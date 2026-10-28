"""DERA Reverse Engineering — Phase 6.1 Namespace Model.

Re-exports CanonicalNamespace with domain-level type alias NamespaceRepresentation.
Preserves native namespace semantics across PostgreSQL, SQLite, MySQL, and MariaDB.
"""

from __future__ import annotations

from dera.metadata.models.namespace import CanonicalNamespace

# Type alias representing namespace-level canonical schema object
NamespaceRepresentation = CanonicalNamespace

__all__ = ["CanonicalNamespace", "NamespaceRepresentation"]
