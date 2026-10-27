"""DERA Database — Repository Layer Foundation.

Provides typed async repository abstractions bound to an explicit AsyncSession,
enabling clean query construction without implicit commits or hidden side effects.
"""

from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from dera_api.db.base import Base
from dera_api.db.models.platform import PlatformMetadata


class BaseRepository[ModelT: Base]:
    """Generic async repository bound to an explicit session."""

    def __init__(self, session: AsyncSession, model_cls: type[ModelT]) -> None:
        self.session = session
        self.model_cls = model_cls


class PlatformMetadataRepository(BaseRepository[PlatformMetadata]):
    """Authoritative repository for platform operational metadata."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, PlatformMetadata)

    async def get_by_key(self, key: str) -> PlatformMetadata | None:
        """Retrieve a metadata record by its unique key.

        Parameters
        ----------
        key : str
            Identifier key to look up.

        Returns
        -------
        PlatformMetadata | None
            Found record or None.
        """
        stmt = select(PlatformMetadata).where(PlatformMetadata.key == key)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def set_value(
        self,
        key: str,
        value: str,
        description: str | None = None,
    ) -> PlatformMetadata:
        """Create or update a metadata record.

        Parameters
        ----------
        key : str
            Unique key identifier.
        value : str
            Value to persist.
        description : str | None
            Optional description.

        Returns
        -------
        PlatformMetadata
            The persisted record instance.
        """
        existing = await self.get_by_key(key)
        now = datetime.now(UTC)
        if existing is not None:
            existing.value = value
            if description is not None:
                existing.description = description
            existing.updated_at = now
            return existing

        record = PlatformMetadata(
            key=key,
            value=value,
            description=description,
            created_at=now,
            updated_at=now,
        )
        self.session.add(record)
        return record

    async def list_all(self) -> Sequence[PlatformMetadata]:
        """List all platform metadata records ordered by key.

        Returns
        -------
        Sequence[PlatformMetadata]
            Ordered list of metadata records.
        """
        stmt = select(PlatformMetadata).order_by(PlatformMetadata.key)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def delete_by_key(self, key: str) -> bool:
        """Delete a metadata record by key.

        Parameters
        ----------
        key : str
            Identifier key to remove.

        Returns
        -------
        bool
            True if a record was deleted, False otherwise.
        """
        stmt = delete(PlatformMetadata).where(PlatformMetadata.key == key)
        result = await self.session.execute(stmt)
        return bool(result.rowcount and result.rowcount > 0)
