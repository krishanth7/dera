"""Abstract Dialect Renderer Base Class.

Defines the required interface for dialect-specific SQL rendering.
"""

from abc import ABC, abstractmethod

from dera.migration.planning.models import AbstractMigrationOperation
from dera.migration.sql.enums import SqlDialectType
from dera.migration.sql.models import GeneratedSqlStatement


class DialectRenderer(ABC):
    """Abstract base class for all SQL dialect compilers."""

    @property
    @abstractmethod
    def dialect(self) -> SqlDialectType:
        """Dialect type implemented by this renderer."""
        pass

    @abstractmethod
    def render_operation(
        self,
        operation: AbstractMigrationOperation,
        target_version: str | None = None,
    ) -> list[GeneratedSqlStatement]:
        """Compile an abstract migration operation into 1+ verified dialect statements."""
        pass
