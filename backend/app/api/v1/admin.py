from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import CurrentUser, require_reviewer
from app.db.session import get_async_session
from app.models.ai_analysis import AIAnalysis
from app.models.audit import AuditLog
from app.models.data_source import DataSource
from app.models.media_asset import MediaAsset
from app.models.moderation import ModerationAction
from app.models.report import Report
from app.models.risk_cell import RiskCell
from app.models.segmentation import SegmentationAsset
from app.schemas.admin import (
    AdminReportDetail,
    AdminReportListItem,
    AdminReportList,
    AnalyticsOverview,
    DataSourceStatusItem,
    DataSourceStatusList,
    HotspotItem,
    HotspotList,
    MediaAssetSummary,
    ModelStatusItem,
    ModelStatusList,
    ModerationActionSummary,
    ReportStatusUpdate,
    VerifyReportRequest,
)

router = APIRouter(prefix="/admin", tags=["admin"])
settings = get_settings()


def _check_moderator(user: CurrentUser) -> None:
    if not user.is_staff:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Requires reviewer or higher role",
        )


@router.get("/reports", response_model=AdminReportList)
async def list_admin_reports(
    status_filter: str | None = Query(default=None, alias="status"),
    hazard_type: str | None = Query(default=None, alias="hazard"),
    cursor: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_async_session),
    user: CurrentUser = Depends(require_reviewer),
):
    """List all reports for moderation — includes private details."""
    query = select(Report).order_by(Report.submitted_at.desc()).limit(limit + 1)

    if status_filter:
        query = query.where(Report.status == status_filter)
    if hazard_type:
        query = query.where(Report.hazard_type == hazard_type)

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
    items_rows = reports[:limit]

    # Get media and AI analysis counts for each report
    item_list = []
    for r in items_rows:
        media_count_result = await db.execute(
            select(func.count(MediaAsset.id)).where(MediaAsset.report_id == r.id)
        )
        media_count = media_count_result.scalar() or 0

        ai_count_result = await db.execute(
            select(func.count(AIAnalysis.id)).where(AIAnalysis.report_id == r.id)
        )
        ai_count = ai_count_result.scalar() or 0

        item_list.append(
            AdminReportListItem(
                id=r.id,
                report_type=r.report_type,
                hazard_type=r.hazard_type,
                severity=r.severity,
                status=r.status,
                latitude=r.latitude,
                longitude=r.longitude,
                reported_at=r.reported_at,
                submitted_at=r.submitted_at,
                is_synthetic=r.is_synthetic,
                media_count=media_count,
                ai_analysis_count=ai_count,
            )
        )

    next_cursor = None
    if has_more and item_list:
        next_cursor = items_rows[-1].submitted_at.isoformat()

    return AdminReportList(items=item_list, next_cursor=next_cursor, has_more=has_more)


@router.get("/reports/{report_id}", response_model=AdminReportDetail)
async def get_admin_report_detail(
    report_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_session),
    user: CurrentUser = Depends(require_reviewer),
):
    """Full report detail with media, AI findings, and moderation history."""
    report = await db.get(Report, report_id)
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    # Get media assets
    media_result = await db.execute(
        select(MediaAsset).where(MediaAsset.report_id == report_id)
    )
    media_assets = media_result.scalars().all()

    # Get AI analyses
    ai_result = await db.execute(
        select(AIAnalysis).where(AIAnalysis.report_id == report_id).order_by(AIAnalysis.created_at.desc())
    )
    ai_analyses = ai_result.scalars().all()

    # Get segmentations for media assets
    seg_list = []
    for ma in media_assets:
        seg_result = await db.execute(
            select(SegmentationAsset).where(SegmentationAsset.media_asset_id == ma.id)
        )
        segs = seg_result.scalars().all()
        seg_list.extend(segs)

    # Get moderation actions
    mod_result = await db.execute(
        select(ModerationAction).where(ModerationAction.report_id == report_id).order_by(ModerationAction.created_at.desc())
    )
    mod_actions = mod_result.scalars().all()

    return AdminReportDetail(
        id=report.id,
        reporter_user_id=report.reporter_user_id,
        organisation_id=report.organisation_id,
        report_type=report.report_type,
        description=report.description,
        latitude=report.latitude,
        longitude=report.longitude,
        reported_at=report.reported_at,
        submitted_at=report.submitted_at,
        status=report.status,
        source_channel=report.source_channel,
        is_synthetic=report.is_synthetic,
        duplicate_of_report_id=report.duplicate_of_report_id,
        hazard_type=report.hazard_type,
        severity=report.severity,
        landmark=report.landmark,
        water_level=report.water_level,
        affects_roads=report.affects_roads,
        affects_homes=report.affects_homes,
        affects_shops=report.affects_shops,
        affects_facilities=report.affects_facilities,
        reporter_contact=report.reporter_contact,
        privacy_consent=report.privacy_consent,
        voice_transcript=report.voice_transcript,
        created_at=report.created_at,
        media_assets=[
            MediaAssetSummary(
                id=ma.id,
                media_type=ma.media_type,
                mime_type=ma.mime_type,
                file_size=ma.file_size,
                processing_status=ma.processing_status,
                uploaded_at=ma.uploaded_at,
                public_thumbnail_key=ma.public_thumbnail_key,
            )
            for ma in media_assets
        ],
        ai_analyses=ai_analyses,
        segmentations=seg_list,
        moderation_history=[
            ModerationActionSummary(
                id=ma.id,
                action=ma.action,
                reason=ma.reason,
                previous_status=ma.previous_status,
                new_status=ma.new_status,
                moderator_user_id=ma.moderator_user_id,
                created_at=ma.created_at,
            )
            for ma in mod_actions
        ],
    )


@router.patch("/reports/{report_id}/status")
async def update_report_status(
    report_id: uuid.UUID,
    body: ReportStatusUpdate,
    db: AsyncSession = Depends(get_async_session),
    user: CurrentUser = Depends(require_reviewer),
):
    """Update a report's status (moderation action)."""
    report = await db.get(Report, report_id)
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    valid_statuses = ["submitted", "under_review", "verified", "rejected", "duplicate"]
    if body.status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"status must be one of: {', '.join(valid_statuses)}",
        )

    previous_status = report.status
    report.status = body.status

    # Record moderation action
    actor_id = None
    if hasattr(user, "user_id") and user.user_id:
        try:
            actor_id = uuid.UUID(user.user_id) if isinstance(user.user_id, str) else user.user_id
        except (ValueError, AttributeError):
            pass
    action = ModerationAction(
        id=uuid.uuid4(),
        report_id=report_id,
        moderator_user_id=actor_id,
        action="status_change",
        reason=body.reason,
        previous_status=previous_status,
        new_status=body.status,
    )
    db.add(action)

    # Record audit log
    audit = AuditLog(
        id=uuid.uuid4(),
        actor_user_id=actor_id,
        action="report_status_change",
        resource_type="report",
        resource_id=str(report_id),
        metadata_={"previous_status": previous_status, "new_status": body.status, "reason": body.reason},
    )
    db.add(audit)

    return {"id": str(report_id), "status": body.status, "previous_status": previous_status}


@router.post("/reports/{report_id}/verify")
async def verify_report(
    report_id: uuid.UUID,
    body: VerifyReportRequest,
    db: AsyncSession = Depends(get_async_session),
    user: CurrentUser = Depends(require_reviewer),
):
    """Verify a report — marks it as verified and records moderation action."""
    report = await db.get(Report, report_id)
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    previous_status = report.status
    report.status = "verified"

    actor_id = None
    if hasattr(user, "user_id") and user.user_id:
        try:
            actor_id = uuid.UUID(user.user_id) if isinstance(user.user_id, str) else user.user_id
        except (ValueError, AttributeError):
            pass

    action = ModerationAction(
        id=uuid.uuid4(),
        report_id=report_id,
        moderator_user_id=actor_id,
        action="verify",
        reason=body.reason,
        previous_status=previous_status,
        new_status="verified",
    )
    db.add(action)

    audit = AuditLog(
        id=uuid.uuid4(),
        actor_user_id=actor_id,
        action="report_verified",
        resource_type="report",
        resource_id=str(report_id),
        metadata_={"reason": body.reason},
    )
    db.add(audit)

    return {"id": str(report_id), "status": "verified", "verified_by": user.user_id}


@router.post("/reports/{report_id}/reanalyze", status_code=status.HTTP_202_ACCEPTED)
async def reanalyze_report(
    report_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_session),
    user: CurrentUser = Depends(require_reviewer),
):
    """Re-enqueue AI analysis for a report's media."""
    report = await db.get(Report, report_id)
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    # Reset media asset processing status
    result = await db.execute(
        select(MediaAsset).where(MediaAsset.report_id == report_id)
    )
    assets = result.scalars().all()
    for asset in assets:
        asset.processing_status = "queued"

    audit = AuditLog(
        id=uuid.uuid4(),
        actor_user_id=user.user_id if hasattr(user, "user_id") else None,
        action="report_reanalyze",
        resource_type="report",
        resource_id=str(report_id),
    )
    db.add(audit)

    return {"id": str(report_id), "message": "Reanalysis enqueued", "media_count": len(assets)}


@router.get("/hotspots", response_model=HotspotList)
async def get_hotspots(
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_async_session),
    user: CurrentUser = Depends(require_reviewer),
):
    """Get prioritised hotspot list."""
    query = (
        select(RiskCell)
        .where(RiskCell.risk_band.in_(["elevated", "high", "very_high"]))
        .order_by(RiskCell.risk_score.desc())
        .limit(limit)
    )
    result = await db.execute(query)
    cells = result.scalars().all()

    # Count reports near each cell
    items = []
    for cell in cells:
        # Count reports within a rough radius
        report_result = await db.execute(
            select(func.count(Report.id)).where(
                Report.status.in_(["submitted", "under_review", "verified"]),
                Report.latitude.between(cell.latitude - 0.01, cell.latitude + 0.01),
                Report.longitude.between(cell.longitude - 0.01, cell.longitude + 0.01),
            )
        )
        report_count = report_result.scalar() or 0

        top_factors = []
        if cell.contributing_factors:
            for f in cell.contributing_factors[:3]:
                if isinstance(f, dict):
                    top_factors.append(f.get("dimension", str(f)))
                else:
                    top_factors.append(str(f))

        items.append(
            HotspotItem(
                risk_cell_id=cell.id,
                grid_index=cell.grid_index,
                latitude=cell.latitude,
                longitude=cell.longitude,
                risk_score=cell.risk_score,
                risk_band=cell.risk_band,
                confidence_score=cell.confidence_score,
                report_count=report_count,
                last_evidence_at=cell.calculated_at,
                top_contributing_factors=top_factors,
                is_illustrative=cell.is_illustrative,
            )
        )

    return HotspotList(items=items, total=len(items))


@router.get("/analytics/overview", response_model=AnalyticsOverview)
async def get_analytics_overview(
    db: AsyncSession = Depends(get_async_session),
    user: CurrentUser = Depends(require_reviewer),
):
    """Dashboard analytics overview with KPI cards."""
    now = datetime.now(timezone.utc)
    period_start = now - timedelta(days=30)

    # Total reports
    total_result = await db.execute(select(func.count(Report.id)))
    total_reports = total_result.scalar() or 0

    # Verified incidents
    verified_result = await db.execute(
        select(func.count(Report.id)).where(Report.status == "verified")
    )
    verified_incidents = verified_result.scalar() or 0

    # Pending review
    pending_result = await db.execute(
        select(func.count(Report.id)).where(Report.status == "submitted")
    )
    pending_review = pending_result.scalar() or 0

    # Open reports
    open_result = await db.execute(
        select(func.count(Report.id)).where(Report.status.in_(["submitted", "under_review"]))
    )
    open_reports = open_result.scalar() or 0

    # Rejected
    rejected_result = await db.execute(
        select(func.count(Report.id)).where(Report.status == "rejected")
    )
    rejected_reports = rejected_result.scalar() or 0

    # Duplicates
    dup_result = await db.execute(
        select(func.count(Report.id)).where(Report.status == "duplicate")
    )
    duplicate_reports = dup_result.scalar() or 0

    # High/very high risk zones
    high_result = await db.execute(
        select(func.count(RiskCell.id)).where(RiskCell.risk_band == "high")
    )
    high_risk_zones = high_result.scalar() or 0

    vhigh_result = await db.execute(
        select(func.count(RiskCell.id)).where(RiskCell.risk_band == "very_high")
    )
    very_high_risk_zones = vhigh_result.scalar() or 0

    # AI analyses
    ai_total_result = await db.execute(select(func.count(AIAnalysis.id)))
    ai_total = ai_total_result.scalar() or 0

    ai_pending_result = await db.execute(
        select(func.count(AIAnalysis.id)).where(AIAnalysis.status.in_(["pending", "queued", "processing"]))
    )
    ai_pending = ai_pending_result.scalar() or 0

    ai_failed_result = await db.execute(
        select(func.count(AIAnalysis.id)).where(AIAnalysis.status == "failed")
    )
    ai_failed = ai_failed_result.scalar() or 0

    ai_completed = ai_total - ai_pending - ai_failed

    # Rainfall source freshness
    rainfall_result = await db.execute(
        select(DataSource).where(DataSource.source_type == "rainfall").limit(1)
    )
    rainfall_source = rainfall_result.scalar_one_or_none()
    rainfall_fresh = False
    rainfall_last_updated = None
    if rainfall_source and rainfall_source.last_success_at:
        rainfall_last_updated = rainfall_source.last_success_at
        rainfall_fresh = (now - rainfall_source.last_success_at).total_seconds() < 86400  # 24h

    return AnalyticsOverview(
        total_reports=total_reports,
        verified_incidents=verified_incidents,
        pending_review=pending_review,
        high_risk_zones=high_risk_zones,
        very_high_risk_zones=very_high_risk_zones,
        open_reports=open_reports,
        rejected_reports=rejected_reports,
        duplicate_reports=duplicate_reports,
        ai_analyses_completed=ai_completed,
        ai_analyses_pending=ai_pending,
        ai_analyses_failed=ai_failed,
        rainfall_source_fresh=rainfall_fresh,
        rainfall_last_updated=rainfall_last_updated,
        period_start=period_start,
        period_end=now,
    )


@router.get("/model-status", response_model=ModelStatusList)
async def get_model_status(
    db: AsyncSession = Depends(get_async_session),
    user: CurrentUser = Depends(require_reviewer),
):
    """Get AI model adapter statuses."""
    items = [
        ModelStatusItem(
            id="muse_spark",
            name="Muse Spark",
            model_id=settings.MUSE_SPARK_MODEL,
            provider_type="hosted_meta",
            status="connected" if settings.MODEL_API_KEY and settings.AI_PROVIDER_MODE.value == "live" else "demo_mode" if settings.DEMO_MODE else "not_configured",
            enabled=settings.ENABLE_AI_IMAGE_ANALYSIS,
            endpoint=settings.MODEL_API_BASE_URL if settings.MODEL_API_KEY else None,
        ),
        ModelStatusItem(
            id="muse_wonder",
            name="Muse Wonder",
            model_id=settings.MUSE_WONDER_MODEL,
            provider_type="hosted_meta",
            status="connected" if settings.MODEL_API_KEY and settings.ENABLE_MUSE_WONDER_ANALYST else "not_configured",
            enabled=settings.ENABLE_MUSE_WONDER_ANALYST,
        ),
        ModelStatusItem(
            id="muse_image",
            name="Muse Image",
            model_id=settings.MUSE_IMAGE_MODEL,
            provider_type="hosted_meta",
            status="not_configured",
            enabled=settings.ENABLE_MUSE_IMAGE_GENERATION,
        ),
        ModelStatusItem(
            id="muse_voice",
            name="Muse Voice Transcribe",
            model_id=settings.MUSE_VOICE_MODEL,
            provider_type="hosted_meta",
            status="connected" if settings.MODEL_API_KEY and settings.ENABLE_AI_VOICE_TRANSCRIPTION else "not_configured",
            enabled=settings.ENABLE_AI_VOICE_TRANSCRIPTION,
        ),
        ModelStatusItem(
            id="sam",
            name="SAM 3.1",
            model_id=settings.SAM_MODEL,
            provider_type="hosted_meta",
            status="not_configured",
            enabled=settings.ENABLE_SAM_SEGMENTATION,
        ),
        ModelStatusItem(
            id="muse_glimmer",
            name="Muse Glimmer (Open-Weight)",
            model_id=settings.MUSE_GLIMMER_MODEL or "not_set",
            provider_type="open_weight",
            status="connected" if settings.MUSE_GLIMMER_ENABLED and settings.MUSE_GLIMMER_BASE_URL else "not_configured",
            enabled=settings.MUSE_GLIMMER_ENABLED,
            endpoint=settings.MUSE_GLIMMER_BASE_URL if settings.MUSE_GLIMMER_ENABLED else None,
        ),
        ModelStatusItem(
            id="muse_spark_open",
            name="Muse Spark Open (Open-Weight)",
            model_id=settings.MUSE_SPARK_OPEN_MODEL or "not_set",
            provider_type="open_weight",
            status="connected" if settings.MUSE_SPARK_OPEN_ENABLED and settings.MUSE_SPARK_OPEN_BASE_URL else "not_configured",
            enabled=settings.MUSE_SPARK_OPEN_ENABLED,
            endpoint=settings.MUSE_SPARK_OPEN_BASE_URL if settings.MUSE_SPARK_OPEN_ENABLED else None,
        ),
    ]

    return ModelStatusList(
        items=items,
        ai_provider_mode=settings.AI_PROVIDER_MODE.value,
        demo_mode=settings.DEMO_MODE,
    )


@router.get("/data-source-status", response_model=DataSourceStatusList)
async def get_data_source_status(
    db: AsyncSession = Depends(get_async_session),
    user: CurrentUser = Depends(require_reviewer),
):
    """Get environmental data source statuses."""
    result = await db.execute(select(DataSource).order_by(DataSource.source_type))
    sources = result.scalars().all()

    return DataSourceStatusList(
        items=[
            DataSourceStatusItem(
                id=s.id,
                name=s.name,
                source_type=s.source_type,
                status=s.status,
                licence=s.licence,
                attribution=s.attribution,
                last_success_at=s.last_success_at,
                update_frequency=s.update_frequency,
                limitations=s.limitations,
            )
            for s in sources
        ]
    )
