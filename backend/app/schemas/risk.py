from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ContributingFactor(BaseModel):
    """A single contributing factor to a risk score."""

    dimension: str = Field(..., description="Risk dimension name")
    raw_value: float = Field(..., description="Raw normalised score for this dimension (0-1)")
    weighted_score: float = Field(..., description="Weighted contribution to total score")
    max_weight: float = Field(..., description="Maximum possible weight for this dimension")
    description: str | None = None


class RiskCellOut(BaseModel):
    """Risk cell response — full detail."""

    id: uuid.UUID
    grid_system: str
    grid_index: str
    latitude: float
    longitude: float
    risk_score: float
    risk_band: str
    confidence_score: float
    data_completeness: float
    contributing_factors: list[ContributingFactor] | None = None
    missing_inputs: list[str] | None = None
    source_ids: list[str] | None = None
    calculation_version: str
    calculated_at: datetime
    valid_until: datetime | None = None
    is_illustrative: bool = False


class RiskCellListItem(BaseModel):
    """Risk cell list item for map display."""

    id: uuid.UUID
    grid_index: str
    latitude: float
    longitude: float
    risk_score: float
    risk_band: str
    confidence_score: float
    data_completeness: float
    is_illustrative: bool = False
    calculated_at: datetime


class RiskCellList(BaseModel):
    """Paginated risk cell list."""

    items: list[RiskCellListItem]
    next_cursor: str | None = None
    has_more: bool = False


class LayerMetadata(BaseModel):
    """Layer metadata for the layers endpoint."""

    id: str
    name: str
    type: str
    visible: bool = True
    source: str | None = None
    last_updated: datetime | None = None
    is_seeded: bool = False
    attribution: str | None = None
