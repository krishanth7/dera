"""DERA API — Base Contract Models and Envelopes.

Provides foundational Pydantic v2 models and generic response wrappers
ensuring deterministic serialization, UTF-8 safety, and consistent metadata.
"""

from typing import TypeVar

from pydantic import BaseModel, ConfigDict, Field

from dera_api.contracts.metadata import ResponseMetadata

T = TypeVar("T")


class DeraBaseModel(BaseModel):
    """Base Pydantic model enforcing deterministic serialization and validation rules."""

    model_config = ConfigDict(
        populate_by_name=True,
        validate_assignment=True,
        ser_json_timedelta="iso8601",
        ser_json_bytes="utf8",
        arbitrary_types_allowed=False,
        extra="ignore",
    )


class DataEnvelope[T](DeraBaseModel):
    """Generic envelope for single-resource API responses with metadata."""

    data: T = Field(..., description="Primary resource payload.")
    meta: ResponseMetadata = Field(
        default_factory=ResponseMetadata,
        description="Response metadata and correlation tracking.",
    )


class CollectionEnvelope[T](DeraBaseModel):
    """Generic envelope for unpaginated collections of resources."""

    items: list[T] = Field(..., description="Collection of resource items.")
    total: int = Field(..., ge=0, description="Total count of items in the collection.")
    meta: ResponseMetadata = Field(
        default_factory=ResponseMetadata,
        description="Response metadata and correlation tracking.",
    )

    @property
    def count(self) -> int:
        return self.total

    @property
    def data(self) -> list[T]:
        return self.items

    @classmethod
    def create(
        cls, items: list[T], meta: ResponseMetadata | None = None
    ) -> "CollectionEnvelope[T]":
        """Factory method to construct a collection envelope with automatic item counting."""
        return cls(items=items, total=len(items), meta=meta or ResponseMetadata())
