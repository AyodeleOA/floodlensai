from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class HazardDetection(BaseModel):
    """A single hazard detected in an image."""

    type: Literal[
        "floodwater", "blocked_drain", "overflowing_drain",
        "damaged_road", "exposed_infrastructure", "other",
    ]
    visible_evidence: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    severity_observation: Literal["low", "moderate", "high", "critical", "unknown"]
    bounding_box: list[int] | None = None  # [x1, y1, x2, y2]
    requires_human_verification: bool = True


class MuseSparkAnalysisResult(BaseModel):
    """Normalised Muse Spark analysis output — the internal schema."""

    scene_summary: str
    hazards: list[HazardDetection] = Field(default_factory=list)
    water_presence: Literal["none", "possible", "visible", "extensive", "uncertain"] = "uncertain"
    infrastructure_observations: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    recommended_review_actions: list[str] = Field(default_factory=list)


class AIAnalysisOut(BaseModel):
    """AI analysis record in API responses."""

    id: uuid.UUID
    report_id: uuid.UUID
    media_asset_id: uuid.UUID
    provider: str
    model_id: str
    model_version: str | None = None
    prompt_version: str | None = None
    status: str
    scene_summary: str | None = None
    structured_result: dict[str, Any] | None = None
    confidence: float | None = None
    limitations: list[Any] | None = None
    request_id: str | None = None
    processing_ms: int | None = None
    created_at: datetime


class SegmentationOut(BaseModel):
    """Segmentation result in API responses."""

    id: uuid.UUID
    media_asset_id: uuid.UUID
    provider: str
    model_id: str
    prompt_text: str | None = None
    mask_s3_key: str | None = None
    bounding_boxes: list[Any] | None = None
    object_labels: list[str] | None = None
    created_at: datetime


class TranscriptionStatusOut(BaseModel):
    """Voice transcription status and text."""

    id: uuid.UUID
    status: str  # pending, processing, completed, failed
    transcript: str | None = None
    language: str | None = None
    confidence: float | None = None
    duration_ms: int | None = None
    created_at: datetime
    updated_at: datetime | None = None


class TranscribeRequest(BaseModel):
    """Request voice transcription for uploaded audio."""

    media_asset_id: uuid.UUID
