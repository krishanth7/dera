"""DERA API — Filtering and Sorting Contracts.

Defines typed, allowlist-only filtering and sorting parameters preventing
arbitrary SQL injection and bounding query complexity.
"""

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class SortOrder(StrEnum):
    """Sort direction options."""

    ASC = "asc"
    DESC = "desc"


class SortParams(BaseModel):
    """Query parameter contract for deterministic result sorting."""

    model_config = ConfigDict(frozen=True, populate_by_name=True)

    sort_by: str = Field(
        ...,
        alias="field",
        pattern=r"^[a-zA-Z_][a-zA-Z0-9_]{0,63}$",
        description="Attribute name to sort by (alphanumeric and underscores, max 64 chars).",
    )
    order: SortOrder = Field(
        default=SortOrder.ASC,
        description="Sort direction (asc for ascending, desc for descending).",
    )

    @property
    def field(self) -> str:
        """Alias for sort_by to support canonical contract access."""
        return self.sort_by


class FilterOperator(StrEnum):
    """Allowlisted filtering comparison operators."""

    EQ = "eq"
    NEQ = "neq"
    GT = "gt"
    GTE = "gte"
    LT = "lt"
    LTE = "lte"
    IN = "in"
    LIKE = "like"
    ILIKE = "ilike"
    IS_NULL = "is_null"
    IS_NOT_NULL = "is_not_null"


class FilterCondition(BaseModel):
    """Single field filter expression."""

    model_config = ConfigDict(frozen=True)

    field: str = Field(
        ...,
        pattern=r"^[a-zA-Z_][a-zA-Z0-9_]{0,63}$",
        description="Attribute name to filter on.",
    )
    operator: FilterOperator = Field(
        ...,
        description="Filter comparison operator.",
    )
    value: Any = Field(
        ...,
        description="Comparison value matching attribute type.",
    )


class FilterParams(BaseModel):
    """Container for complex multi-attribute filter sets."""

    model_config = ConfigDict(frozen=True, populate_by_name=True)

    filters: list[FilterCondition] = Field(
        default_factory=list,
        alias="conditions",
        max_length=20,
        description="Bounded list of filter conditions (maximum 20).",
    )

    @property
    def conditions(self) -> list[FilterCondition]:
        """Alias for filters to support canonical contract access."""
        return self.filters
