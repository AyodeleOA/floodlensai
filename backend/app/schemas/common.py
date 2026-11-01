from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field


T = TypeVar("T")


class ErrorResponse(BaseModel):
    error: str = Field(..., description="Error type/short code")
    message: str = Field(..., description="Human-readable error message")
    detail: dict[str, Any] | None = Field(None, description="Additional error detail")


class HealthLiveResponse(BaseModel):
    status: str = "ok"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class HealthReadyResponse(BaseModel):
    status: str = "ok"
    database: str = "connected"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CursorPage(BaseModel, Generic[T]):
    """Cursor-based pagination wrapper."""

    items: list[T]
    next_cursor: str | None = None
    has_more: bool = False
    total: int | None = None


class BBoxParams(BaseModel):
    """Bounding box query parameters."""

    bbox: str | None = Field(None, description="min_lon,min_lat,max_lon,max_lat")


class LayerInfo(BaseModel):
    id: str
    name: str
    type: str
    visible: bool = True
    opacity: float = 1.0
    source: str | None = None
    last_updated: datetime | None = None
    is_seeded: bool = False


class Disclaimer(BaseModel):
    text: str = (
        "FloodLens AI provides community observations and data-informed risk indicators "
        "for situational awareness. It is not an official emergency warning system, "
        "does not guarantee that any location is safe, and does not replace instructions "
        "from emergency-management authorities. Risk estimates may be incomplete or "
        "inaccurate where observations or environmental data are missing, delayed, or "
        "unverified. In an emergency, contact the appropriate local emergency services "
        "and follow official guidance."
    )
