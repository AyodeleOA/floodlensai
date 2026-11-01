from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.ai_analysis import AIAnalysisOut, SegmentationOut
from app.schemas.report import MapReportItem


class AdminReportDetail(BaseModel):
    """Full report detail for authority/moderation view — includes private data."""

    id: uuid.UUID
    reporter_user_id: uuid.UUID | None = None
    organisation_id: uuid.UUID | None = None
    report_type: str
    description: str | None = None
    latitude: float
    longitude: float
    reported_at: datetime | None = None
    submitted_at: datetime
    status: str
    source_channel: str
    is_synthetic: bool = False
    duplicate_of_report_id: uuid.UUID | None = None
    hazard_type: str | None = None
    severity: str | None = None
    landmark: str | None = None
    water_level: str | None = None
    affects_roads: bool | None = None
    affects_homes: bool | None = None
    affects_shops: bool | None = None
    affects_facilities: bool | None = None
    reporter_contact: str | None = None
    privacy_consent: bool = False
    voice_transcript: str | None = None
    created_at: datetime
    media_assets: list[MediaAssetSummary] = Field(default_factory=list)
    ai_analyses: list[AIAnalysisOut] = Field(default_factory=list)
    segmentations: list[SegmentationOut] = Field(default_factory=list)
    moderation_history: list[ModerationActionSummary] = Field(default_factory=list)


class MediaAssetSummary(BaseModel):
    """Media asset summary for admin view."""

    id: uuid.UUID
    media_type: str
    mime_type: str
    file_size: int
    processing_status: str
    uploaded_at: datetime
    public_thumbnail_key: str | None = None


class ModerationActionSummary(BaseModel):
    """Moderation action record in admin responses."""

    id: uuid.UUID
    action: str
    reason: str | None = None
    previous_status: str
    new_status: str
    moderator_user_id: uuid.UUID | None = None
    created_at: datetime


class AdminReportList(BaseModel):
    """Paginated admin report list."""

    items: list[AdminReportListItem]
    next_cursor: str | None = None
    has_more: bool = False
    total: int | None = None


class AdminReportListItem(BaseModel):
    """Report list item for admin queue."""

    id: uuid.UUID
    report_type: str
    hazard_type: str | None = None
    severity: str | None = None
    status: str
    latitude: float
    longitude: float
    reported_at: datetime | None = None
    submitted_at: datetime
    is_synthetic: bool = False
    media_count: int = 0
    ai_analysis_count: int = 0


class ReportStatusUpdate(BaseModel):
    """Patch report status."""

    status: str = Field(..., description="New status: submitted, under_review, verified, rejected, duplicate")
    reason: str | None = Field(None, max_length=1000)


class VerifyReportRequest(BaseModel):
    """Verify a report."""

    reason: str | None = Field(None, max_length=1000)


class HotspotItem(BaseModel):
    """Hotspot list item."""

    risk_cell_id: uuid.UUID
    grid_index: str
    latitude: float
    longitude: float
    risk_score: float
    risk_band: str
    confidence_score: float
    report_count: int
    last_evidence_at: datetime | None = None
    top_contributing_factors: list[str] = Field(default_factory=list)
    is_illustrative: bool = False


class HotspotList(BaseModel):
    """Prioritised hotspot list."""

    items: list[HotspotItem]
    total: int


class AnalyticsOverview(BaseModel):
    """Dashboard analytics overview."""

    total_reports: int
    verified_incidents: int
    pending_review: int
    high_risk_zones: int
    very_high_risk_zones: int
    open_reports: int
    rejected_reports: int
    duplicate_reports: int
    ai_analyses_completed: int
    ai_analyses_pending: int
    ai_analyses_failed: int
    rainfall_source_fresh: bool = False
    rainfall_last_updated: datetime | None = None
    period_start: datetime
    period_end: datetime


class ModelStatusItem(BaseModel):
    """AI model adapter status."""

    id: str
    name: str
    model_id: str
    provider_type: str  # hosted_meta, open_weight, demo
    status: str  # connected, not_configured, unavailable, demo_mode
    enabled: bool = False
    endpoint: str | None = None
    last_health_check: datetime | None = None


class ModelStatusList(BaseModel):
    """All model adapter statuses."""

    items: list[ModelStatusItem]
    ai_provider_mode: str
    demo_mode: bool


class DataSourceStatusItem(BaseModel):
    """Data source status for admin view."""

    id: uuid.UUID
    name: str
    source_type: str
    status: str
    licence: str | None = None
    attribution: str | None = None
    last_success_at: datetime | None = None
    update_frequency: str | None = None
    limitations: str | None = None


class DataSourceStatusList(BaseModel):
    """All data source statuses."""

    items: list[DataSourceStatusItem]


class AdminReportListResponse(BaseModel):
    items: list[MapReportItem]
    next_cursor: str | None = None
    has_more: bool = False
