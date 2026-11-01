from __future__ import annotations

from typing import Any

from fastapi import Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_session


def parse_bbox(bbox: str | None = Query(default=None)) -> tuple[float, float, float, float] | None:
    """Parse a bbox query parameter: min_lon,min_lat,max_lon,max_lat."""
    if bbox is None:
        return None
    parts = bbox.split(",")
    if len(parts) != 4:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="bbox must be 'min_lon,min_lat,max_lon,max_lat'",
        )
    try:
        vals = [float(p) for p in parts]
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="bbox values must be numeric",
        )
    min_lon, min_lat, max_lon, max_lat = vals
    if min_lon < -180 or max_lon > 180 or min_lat < -90 or max_lat > 90:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="bbox coordinates out of valid range",
        )
    if min_lon > max_lon or min_lat > max_lat:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="bbox min values must be less than max values",
        )
    return min_lon, min_lat, max_lon, max_lat


def parse_cursor(cursor: str | None = Query(default=None)) -> str | None:
    """Return a cursor for pagination. Opaque to the client."""
    return cursor


def get_db() -> Any:
    """Return the get_async_session dependency for use in route definitions."""
    return Depends(get_async_session)
