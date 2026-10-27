"""DERA Reverse Engineering — Phase 6.1 Schema Models Subpackage.

Re-exports canonical schema models from dera.metadata while providing
standard representation type aliases for reverse-engineering core consumers.
"""

from __future__ import annotations

from dera.metadata.models.column import CanonicalColumn
from dera.metadata.models.constraint import CanonicalConstraint
from dera.metadata.models.database import CanonicalDatabase
from dera.metadata.models.index import CanonicalIndex, CanonicalIndexTerm
from dera.metadata.models.namespace import CanonicalNamespace
from dera.metadata.models.relationship import CanonicalForeignKey, ForeignKeyMapping
from dera.metadata.models.table import CanonicalTable
from dera.metadata.models.trigger import CanonicalTrigger
from dera.metadata.models.view import CanonicalView
from dera.reverse_engineering.models.column import ColumnRepresentation
from dera.reverse_engineering.models.constraint import ConstraintRepresentation
from dera.reverse_engineering.models.database import DatabaseRepresentation
from dera.reverse_engineering.models.index import IndexRepresentation
from dera.reverse_engineering.models.namespace import NamespaceRepresentation
from dera.reverse_engineering.models.table import TableRepresentation
from dera.reverse_engineering.models.trigger import TriggerRepresentation
from dera.reverse_engineering.models.view import ViewRepresentation

# Foreign key representation alias
ForeignKeyRepresentation = CanonicalForeignKey

__all__ = [
    "CanonicalColumn",
    "CanonicalConstraint",
    "CanonicalDatabase",
    "CanonicalForeignKey",
    "CanonicalIndex",
    "CanonicalIndexTerm",
    "CanonicalNamespace",
    "CanonicalTable",
    "CanonicalTrigger",
    "CanonicalView",
    "ColumnRepresentation",
    "ConstraintRepresentation",
    "DatabaseRepresentation",
    "ForeignKeyMapping",
    "ForeignKeyRepresentation",
    "IndexRepresentation",
    "NamespaceRepresentation",
    "TableRepresentation",
    "TriggerRepresentation",
    "ViewRepresentation",
]
