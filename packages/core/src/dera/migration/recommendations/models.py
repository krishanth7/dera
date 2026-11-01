"""DERA Migration — Phase 9.2 Recommendation Models & Catalog.

Provides strongly typed, evidence-backed advisory engineering recommendations.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class EngineeringRecommendation(BaseModel):
    """Advisory engineering recommendation to mitigate an identified migration risk."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    recommendation_id: str = Field(description="Deterministic recommendation identifier (e.g. 'rec_...').")
    risk_id: str = Field(description="Identifier of the risk assessment being addressed.")
    title: str = Field(description="Concise recommendation title.")
    description: str = Field(description="Detailed suggested action.")
    rationale: str = Field(description="Why this step is necessary before or during migration.")
    suggested_review_actions: tuple[str, ...] = Field(
        default_factory=tuple,
        description="Checklist of specific engineering review steps.",
    )
    applicable_engines: tuple[str, ...] = Field(
        default=("all",),
        description="Database engines where this recommendation applies.",
    )
