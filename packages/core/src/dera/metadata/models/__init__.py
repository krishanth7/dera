"""DERA Canonical Metadata Models Package.

Re-exports all canonical schema models for databases, namespaces, tables,
columns, constraints, relationships, indexes, views, and triggers.
"""

from dera.metadata.models.column import CanonicalColumn
from dera.metadata.models.constraint import CanonicalConstraint
from dera.metadata.models.database import CanonicalDatabase
from dera.metadata.models.index import CanonicalIndex, CanonicalIndexTerm
from dera.metadata.models.namespace import CanonicalNamespace
from dera.metadata.models.relationship import (
    CanonicalForeignKey,
    ForeignKeyMapping,
)
from dera.metadata.models.table import CanonicalTable
from dera.metadata.models.trigger import CanonicalTrigger
from dera.metadata.models.view import CanonicalView

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
    "ForeignKeyMapping",
]
