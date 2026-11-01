from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import parse_cursor, get_db as get_db_dep
from app.core.config import get_settings
from app.core.security import CurrentUser, get_current_user
from app.db.session import get_async_session
from app.models.media_asset import MediaAsset
from app.models.report import Report
from app.schemas.report import (
    MediaCompleteRequest,
    MediaCompleteResponse,
    MediaUploadURLRequest,
    MediaUploadURLResponse,
    PublicReport,
    PublicReportList,
    ReportCreate,
    ReportCreated,
    ReportReceipt,
    VoiceUploadURLRequest,
    VoiceUploadURLResponse,
)
from app.services.media.storage import generate_presigned_upload, get_s3_key_prefix
from app.services.media.validation import validate_mime_type

router = APIRouter(prefix="/reports", tags=["reports"])
settings = get_settings()


def _coarse_coord(coord: float, decimals: int = 2) -> float:
    """Round coordinates to coarse precision for public display."""
    return round(coord, decimals)


@router.post("", response_model=ReportCreated, status_code=status.HTTP_201_CREATED)
async def create_report(
    body: ReportCreate,
    db: AsyncSession = Depends(get_async_session),
    user: CurrentUser = Depends(get_current_user),
):
    """Create a new flood or drainage report (metadata only — media uploaded separately)."""
    report = Report(
        id=uuid.uuid4(),
        reporter_user_id=user.user_id if user.is_authenticated else None,
        report_type=body.report_type,
        description=body.description,
        latitude=body.latitude,
        longitude=body.longitude,
        reported_at=body.reported_at,
        status="submitted",
        source_channel=body.source_channel,
        hazard_type=body.hazard_type,
        severity=body.severity,
        landmark=body.landmark,
        water_level=body.water_level,
        affects_roads=body.affects_roads,
        affects_homes=body.affects_homes,
        affects_shops=body.affects_shops,
        affects_facilities=body.affects_facilities,
        reporter_contact=body.reporter_contact,
        privacy_consent=body.privacy_consent,
        is_synthetic=False,
    )
    db.add(report)
    await db.flush()
    receipt_url = f"/api/v1/reports/{report.id}/receipt"
    return ReportCreated(
        id=report.id,
        status=report.status,
        submitted_at=report.submitted_at,
        receipt_url=receipt_url,
    )


@router.post("/{report_id}/media-upload-url", response_model=MediaUploadURLResponse)
async def get_media_upload_url(
    report_id: uuid.UUID,
    body: MediaUploadURLRequest,
    db: AsyncSession = Depends(get_async_session),
    user: CurrentUser = Depends(get_current_user),
):
    """Request a short-lived presigned S3 upload URL for a photo or video."""
    report = await db.get(Report, report_id)
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    if not validate_mime_type(body.mime_type, body.media_type):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unsupported MIME type: {body.mime_type}",
        )

    media_asset_id = uuid.uuid4()
    s3_key = get_s3_key_prefix(report_id, body.media_type) + f"/{media_asset_id}"

    upload_url, expires_in = generate_presigned_upload(s3_key, body.mime_type)

    # Create media asset record with pending status
    asset = MediaAsset(
        id=media_asset_id,
        report_id=report_id,
        s3_key=s3_key,
        media_type=body.media_type,
        sha256="pending",
        mime_type=body.mime_type,
        file_size=body.file_size,
        captured_at=body.captured_at,
        processing_status="awaiting_upload",
    )
    db.add(asset)
    await db.flush()

    return MediaUploadURLResponse(
        upload_url=upload_url,
        s3_key=s3_key,
        expires_in=expires_in,
        media_asset_id=media_asset_id,
    )


@router.post("/{report_id}/media-complete", response_model=MediaCompleteResponse, status_code=status.HTTP_202_ACCEPTED)
async def confirm_media_upload(
    report_id: uuid.UUID,
    body: MediaCompleteRequest,
    db: AsyncSession = Depends(get_async_session),
    user: CurrentUser = Depends(get_current_user),
):
    """Confirm upload and enqueue AI analysis."""
    report = await db.get(Report, report_id)
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    # Find the pending media asset
    result = await db.execute(
        select(MediaAsset).where(
            MediaAsset.report_id == report_id,
            MediaAsset.sha256 == "pending",
        )
    )
    asset = result.scalar_one_or_none()
    if asset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No pending media upload found for this report",
        )

    # Update asset with confirmed details
    asset.sha256 = body.sha256
    asset.mime_type = body.mime_type
    asset.file_size = body.file_size
    asset.media_type = body.media_type
    asset.captured_at = body.captured_at
    asset.processing_status = "queued"

    # In local mode, analysis is enqueued but may not run synchronously
    analysis_enqueued = settings.AI_PROVIDER_MODE != "mock" or settings.DEMO_MODE

    return MediaCompleteResponse(
        media_asset_id=asset.id,
        processing_status=asset.processing_status,
        analysis_enqueued=analysis_enqueued,
    )


@router.post("/{report_id}/voice-upload-url", response_model=VoiceUploadURLResponse)
async def get_voice_upload_url(
    report_id: uuid.UUID,
    body: VoiceUploadURLRequest,
    db: AsyncSession = Depends(get_async_session),
    user: CurrentUser = Depends(get_current_user),
):
    """Request a presigned S3 upload URL for a voice note."""
    report = await db.get(Report, report_id)
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    media_asset_id = uuid.uuid4()
    s3_key = get_s3_key_prefix(report_id, "voice") + f"/{media_asset_id}"

    upload_url, expires_in = generate_presigned_upload(s3_key, body.mime_type)

    asset = MediaAsset(
        id=media_asset_id,
        report_id=report_id,
        s3_key=s3_key,
        media_type="voice",
        sha256="pending",
        mime_type=body.mime_type,
        file_size=body.file_size,
        processing_status="awaiting_upload",
    )
    db.add(asset)
    await db.flush()

    return VoiceUploadURLResponse(
        upload_url=upload_url,
        s3_key=s3_key,
        expires_in=expires_in,
        media_asset_id=media_asset_id,
    )


@router.get("/{report_id}/receipt", response_model=ReportReceipt)
async def get_report_receipt(
    report_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_session),
):
    """Retrieve a safe submission receipt — no PII."""
    report = await db.get(Report, report_id)
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    # Count media assets
    result = await db.execute(
        select(func.count(MediaAsset.id)).where(MediaAsset.report_id == report_id)
    )
    media_count = result.scalar() or 0

    return ReportReceipt(
        id=report.id,
        status=report.status,
        submitted_at=report.submitted_at,
        report_type=report.report_type,
        hazard_type=report.hazard_type,
        latitude_coarse=_coarse_coord(report.latitude),
        longitude_coarse=_coarse_coord(report.longitude),
        media_count=media_count,
        ai_analysis_status=None,
        is_synthetic=report.is_synthetic,
    )


@router.get("/public", response_model=PublicReportList)
async def list_public_reports(
    db: AsyncSession = Depends(get_async_session),
    cursor: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
):
    """Public-safe report list with coarse location and redacted details."""
    query = (
        select(Report)
        .where(Report.status.in_(["submitted", "under_review", "verified"]))
        .order_by(Report.submitted_at.desc())
        .limit(limit + 1)
    )

    if cursor:
        try:
            cursor_dt = datetime.fromisoformat(cursor)
            query = query.where(Report.submitted_at < cursor_dt)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid cursor format",
            )

    result = await db.execute(query)
    reports = result.scalars().all()

    has_more = len(reports) > limit
    items = reports[:limit]

    next_cursor = None
    if has_more and items:
        next_cursor = items[-1].submitted_at.isoformat()

    return PublicReportList(
        items=[
            PublicReport(
                id=r.id,
                report_type=r.report_type,
                hazard_type=r.hazard_type,
                severity=r.severity,
                status=r.status,
                latitude_coarse=_coarse_coord(r.latitude),
                longitude_coarse=_coarse_coord(r.longitude),
                reported_at=r.reported_at,
                submitted_at=r.submitted_at,
                is_synthetic=r.is_synthetic,
            )
            for r in items
        ],
        next_cursor=next_cursor,
        has_more=has_more,
    )
