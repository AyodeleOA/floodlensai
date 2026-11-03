from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator


class ReportCreate(BaseModel):
    """Request body for creating a new report."""

    report_type: str = Field(..., max_length=100, description="Hazard category: flooding, drainage, road_damage, etc.")
    description: str | None = Field(None, max_length=5000)
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    reported_at: datetime | None = None
    source_channel: str = Field("web", max_length=50)
    hazard_type: str | None = Field(None, max_length=100)
    severity: str | None = Field(None, max_length=50, description="low, moderate, high, critical")
    landmark: str | None = Field(None, max_length=255)
    water_level: str | None = Field(None, max_length=50, description="ankle, knee, waist, above_waist")
    affects_roads: bool | None = None
    affects_homes: bool | None = None
    affects_shops: bool | None = None
    affects_facilities: bool | None = None
    reporter_contact: str | None = Field(None, max_length=255, description="Private — never exposed publicly")
    privacy_consent: bool = Field(False, description="User must acknowledge privacy notice")
    idempotency_key: str | None = Field(None, max_length=255)

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, v: str | None) -> str | None:
        if v is not None and v not in ("low", "moderate", "high", "critical", "unknown"):
            raise ValueError("severity must be one of: low, moderate, high, critical, unknown")
        return v

    @field_validator("water_level")
    @classmethod
    def validate_water_level(cls, v: str | None) -> str | None:
        if v is not None and v not in ("ankle", "knee", "waist", "above_waist"):
            raise ValueError("water_level must be one of: ankle, knee, waist, above_waist")
        return v


class ReportCreated(BaseModel):
    """Response after report creation."""

    id: uuid.UUID
    status: str
    submitted_at: datetime
    receipt_url: str


class MediaUploadURLRequest(BaseModel):
    """Request a presigned S3 upload URL."""

    mime_type: str = Field(..., max_length=100)
    file_size: int = Field(..., gt=0, le=100_000_000, description="File size in bytes (max 100MB)")
    media_type: str = Field("photo", max_length=50, description="photo, video, or voice")
    captured_at: datetime | None = None


class MediaUploadURLResponse(BaseModel):
    """Presigned S3 upload URL response."""

    upload_url: str
    s3_key: str
    expires_in: int = Field(default=3600, description="URL expiry in seconds")
    media_asset_id: uuid.UUID


class MediaCompleteRequest(BaseModel):
    """Confirm upload and enqueue analysis."""

    s3_key: str = Field(..., max_length=512)
    sha256: str = Field(..., min_length=64, max_length=64)
    mime_type: str = Field(..., max_length=100)
    file_size: int = Field(..., gt=0)
    media_type: str = Field("photo", max_length=50)
    captured_at: datetime | None = None
    idempotency_key: str | None = Field(None, max_length=255)


class MediaCompleteResponse(BaseModel):
    """Response after media upload confirmation."""

    media_asset_id: uuid.UUID
    processing_status: str
    analysis_enqueued: bool
    analysis_status: str | None = None
    analysis_provider: str | None = None
    analysis_error: str | None = None
    is_demo_analysis: bool = False


class VoiceUploadURLRequest(BaseModel):
    """Request a presigned voice upload URL."""

    mime_type: str = Field("audio/webm", max_length=100)
    file_size: int = Field(..., gt=0, le=25_000_000, description="Voice file max 25MB")


class VoiceUploadURLResponse(BaseModel):
    """Presigned S3 voice upload URL response."""

    upload_url: str
    s3_key: str
    expires_in: int = 3600
    media_asset_id: uuid.UUID


class ReportReceipt(BaseModel):
    """Safe submission receipt — no PII."""

    id: uuid.UUID
    status: str
    submitted_at: datetime
    report_type: str
    hazard_type: str | None
    # Coarse location only (2 decimal places ≈ ~1.1km)
    latitude_coarse: float = Field(..., description="Coarse latitude for public display")
    longitude_coarse: float = Field(..., description="Coarse longitude for public display")
    media_count: int = 0
    ai_analysis_status: str | None = None
    is_synthetic: bool = False


class PublicReport(BaseModel):
    """Public-safe report list item — redacted details, coarse coordinates."""

    id: uuid.UUID
    report_type: str
    hazard_type: str | None
    severity: str | None
    status: str
    latitude_coarse: float
    longitude_coarse: float
    reported_at: datetime | None
    submitted_at: datetime
    is_synthetic: bool = False


class PublicReportList(BaseModel):
    """Paginated public report list."""

    items: list[PublicReport]
    next_cursor: str | None = None
    has_more: bool = False


class MapReportItem(BaseModel):
    """Report item for map display."""

    id: uuid.UUID
    report_type: str
    hazard_type: str | None
    severity: str | None
    status: str
    latitude: float
    longitude: float
    reported_at: datetime | None
    submitted_at: datetime
    is_synthetic: bool = False


class MapSummary(BaseModel):
    """Summary of map data within a bounding box."""

    total_reports: int
    verified_incidents: int
    pending_reports: int
    high_risk_cells: int
    last_updated: datetime
    bbox: str
    is_seeded: bool = False
