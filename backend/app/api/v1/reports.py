from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import parse_cursor, get_db as get_db_dep
from app.core.config import get_settings
from app.core.security import CurrentUser, get_current_user
from app.db.session import get_async_session
from app.models.ai_analysis import AIAnalysis
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

    # Find the pending media asset by s3_key (unique per upload)
    result = await db.execute(
        select(MediaAsset).where(
            MediaAsset.report_id == report_id,
            MediaAsset.s3_key == body.s3_key,
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
    await db.flush()

    # Run analysis for photo/video media (voice uses transcribe endpoint)
    analysis_enqueued = False
    analysis_status: str | None = None
    analysis_provider: str | None = None
    analysis_error: str | None = None
    is_demo_analysis = False

    if body.media_type in ("photo", "video"):
        # In production with SQS configured, enqueue to SQS for async processing.
        # In demo/mock mode, run analysis synchronously inline.
        sqs_url = settings.SQS_MEDIA_ANALYSIS_QUEUE_URL

        if sqq_url := sqs_url:
            # Async path: send message to SQS for the worker Lambda
            try:
                import boto3
                sqs = boto3.client("sqs", region_name=settings.AWS_REGION)
                sqs.send_message(
                    QueueUrl=sqq_url,
                    MessageBody=json.dumps({"media_asset_id": str(asset.id)}),
                )
                analysis_enqueued = True
                analysis_status = "queued"
                asset.processing_status = "queued"
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"SQS enqueue failed: {e}", exc_info=True)
                # Fall back to sync analysis
                try:
                    from app.workers.media_analysis import process_media_asset
                    result = await process_media_asset(asset.id, db)
                    analysis_status = result.get("status")
                    analysis_provider = result.get("provider")
                    is_demo_analysis = result.get("is_demo", False)
                    analysis_enqueued = analysis_status in ("completed", "processing")
                    asset.processing_status = analysis_status or "queued"
                except Exception as e2:
                    asset.processing_status = "analysis_failed"
                    analysis_error = str(e2)[:500]
        else:
            # Sync path: run analysis inline (demo/mock mode)
            try:
                from app.workers.media_analysis import process_media_asset
                result = await process_media_asset(asset.id, db)
                analysis_status = result.get("status")
                analysis_provider = result.get("provider")
                is_demo_analysis = result.get("is_demo", False)
                analysis_enqueued = analysis_status in ("completed", "processing")
                asset.processing_status = analysis_status or "queued"
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Media analysis failed: {e}", exc_info=True)
                asset.processing_status = "analysis_failed"
                analysis_error = str(e)[:500]
    else:
        # Voice or other media — analysis runs via transcribe endpoint
        analysis_enqueued = True

    return MediaCompleteResponse(
        media_asset_id=asset.id,
        processing_status=asset.processing_status,
        analysis_enqueued=analysis_enqueued,
        analysis_status=analysis_status,
        analysis_provider=analysis_provider,
        analysis_error=analysis_error,
        is_demo_analysis=is_demo_analysis,
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

    # Query AI analysis status for this report's media
    ai_status: str | None = None
    if media_count > 0:
        ai_result = await db.execute(
            select(AIAnalysis)
            .where(AIAnalysis.report_id == report_id)
            .order_by(AIAnalysis.created_at.desc())
            .limit(1)
        )
        ai_analysis = ai_result.scalar_one_or_none()
        if ai_analysis is not None:
            ai_status = ai_analysis.status
        else:
            # No AI analysis records yet — check if any media is queued
            media_result = await db.execute(
                select(MediaAsset.processing_status)
                .where(MediaAsset.report_id == report_id)
                .order_by(MediaAsset.uploaded_at.desc())
                .limit(1)
            )
            latest_status = media_result.scalar_one_or_none()
            if latest_status == "queued":
                ai_status = "pending"
            elif latest_status == "processing":
                ai_status = "processing"

    return ReportReceipt(
        id=report.id,
        status=report.status,
        submitted_at=report.submitted_at,
        report_type=report.report_type,
        hazard_type=report.hazard_type,
        latitude_coarse=_coarse_coord(report.latitude),
        longitude_coarse=_coarse_coord(report.longitude),
        media_count=media_count,
        ai_analysis_status=ai_status,
        is_synthetic=report.is_synthetic,
    )


@router.post("/analyze-test", status_code=status.HTTP_200_OK)
async def analyze_test(
    body: dict,
    db: AsyncSession = Depends(get_async_session),
):
    """Direct test endpoint for media analysis.

    Two usage modes:

    1. Pass an existing media_asset_id to test analysis on a real uploaded file:
       {"media_asset_id": "uuid-of-existing-asset"}

    2. Pass raw fields to create a temporary asset and run analysis:
       {"report_id": "uuid", "s3_key": "reports/.../photo/...", "sha256": "...", "mime_type": "image/jpeg", "file_size": 47103, "media_type": "photo"}
       (If report_id is omitted, a synthetic test report is created.)

    Returns the full analysis result including scene summary and hazards.
    AI analysis is stored in the database for persistence.
    """
    from app.workers.media_analysis import process_media_asset

    # Mode 1: use an existing media asset
    if "media_asset_id" in body:
        try:
            existing_asset_id = uuid.UUID(body["media_asset_id"])
        except ValueError:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid media_asset_id")
        existing_asset = await db.get(MediaAsset, existing_asset_id)
        if existing_asset is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media asset not found")
        existing_asset.processing_status = "queued"
        await db.flush()
        result = await process_media_asset(existing_asset_id, db)
        return {
            "media_asset_id": str(existing_asset_id),
            "report_id": str(existing_asset.report_id),
            "s3_key": existing_asset.s3_key,
            "analysis_result": result,
            "status": result.get("status"),
        }

    # Mode 2: create a temporary asset with the provided fields
    report_id_str = body.get("report_id")
    if report_id_str:
        try:
            report_id = uuid.UUID(report_id_str)
            report = await db.get(Report, report_id)
            if report is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
        except ValueError:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid report_id")
    else:
        # Create a synthetic test report
        report = Report(
            id=uuid.uuid4(),
            report_type="flooding",
            latitude=6.4541,
            longitude=3.3947,
            status="submitted",
            source_channel="test",
            is_synthetic=True,
            privacy_consent=True,
        )
        db.add(report)
        await db.flush()
        report_id = report.id

    # Create a media asset for the test
    s3_key = body.get("s3_key", "reports/test/photo/test")
    asset = MediaAsset(
        id=uuid.uuid4(),
        report_id=report_id,
        s3_key=s3_key,
        media_type=body.get("media_type", "photo"),
        sha256=body.get("sha256", "0" * 64),
        mime_type=body.get("mime_type", "image/jpeg"),
        file_size=body.get("file_size", 0),
        processing_status="queued",
    )
    db.add(asset)
    await db.flush()

    result = await process_media_asset(asset.id, db)
    return {
        "media_asset_id": str(asset.id),
        "report_id": str(report_id),
        "s3_key": s3_key,
        "analysis_result": result,
        "status": result.get("status"),
    }


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


@router.get("/{report_id}/detail")
async def get_report_detail(
    report_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_session),
):
    """Public report detail — includes media metadata, AI analysis, and voice transcript.

    Returns coarse coordinates only. Private reporter data is not included.
    Media download URLs are short-lived presigned S3 URLs.
    """
    report = await db.get(Report, report_id)
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    # Fetch media assets
    media_result = await db.execute(
        select(MediaAsset).where(MediaAsset.report_id == report_id)
    )
    media_assets = media_result.scalars().all()

    # Build media items with presigned download URLs
    from app.services.media.storage import generate_presigned_download
    media_items = []
    for m in media_assets:
        download_url = generate_presigned_download(m.s3_key, expires_in=900)
        # Only expose public thumbnail or presigned URL — never private contact data
        media_items.append({
            "id": str(m.id),
            "media_type": m.media_type,
            "mime_type": m.mime_type,
            "file_size": m.file_size,
            "processing_status": m.processing_status,
            "uploaded_at": m.uploaded_at.isoformat(),
            "download_url": download_url,
            "public_thumbnail_key": m.public_thumbnail_key,
        })

    # Fetch AI analyses
    ai_result = await db.execute(
        select(AIAnalysis)
        .where(AIAnalysis.report_id == report_id)
        .order_by(AIAnalysis.created_at.desc())
    )
    ai_analyses = ai_result.scalars().all()

    ai_items = []
    for a in ai_analyses:
        ai_items.append({
            "id": str(a.id),
            "provider": a.provider,
            "model_id": a.model_id,
            "status": a.status,
            "scene_summary": a.scene_summary,
            "structured_result": a.structured_result,
            "confidence": a.confidence,
            "limitations": a.limitations,
            "processing_ms": a.processing_ms,
            "created_at": a.created_at.isoformat(),
        })

    return {
        "id": str(report.id),
        "report_type": report.report_type,
        "hazard_type": report.hazard_type,
        "severity": report.severity,
        "status": report.status,
        "description": report.description,
        "landmark": report.landmark,
        "water_level": report.water_level,
        "affects_roads": report.affects_roads,
        "affects_homes": report.affects_homes,
        "affects_shops": report.affects_shops,
        "affects_facilities": report.affects_facilities,
        "latitude_coarse": _coarse_coord(report.latitude),
        "longitude_coarse": _coarse_coord(report.longitude),
        "reported_at": report.reported_at.isoformat() if report.reported_at else None,
        "submitted_at": report.submitted_at.isoformat(),
        "is_synthetic": report.is_synthetic,
        "voice_transcript": report.voice_transcript,
        "media": media_items,
        "ai_analyses": ai_items,
    }
