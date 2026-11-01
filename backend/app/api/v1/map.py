from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import parse_bbox
from app.db.session import get_async_session
from app.models.report import Report
from app.models.risk_cell import RiskCell
from app.models.data_source import DataSource
from app.schemas.report import MapReportItem, MapSummary
from app.schemas.risk import RiskCellListItem, RiskCellList, LayerMetadata

router = APIRouter(prefix="/map", tags=["map"])


@router.get("/summary", response_model=MapSummary)
async def get_map_summary(
    bbox: str | None = Query(default=None, description="min_lon,min_lat,max_lon,max_lat"),
    db: AsyncSession = Depends(get_async_session),
):
    """Summary of map data within a bounding box."""
    bbox_tuple = parse_bbox(bbox) if bbox else None

    # Build query for reports in bbox
    report_query = select(Report).where(Report.status.in_(["submitted", "under_review", "verified"]))
    if bbox_tuple:
        min_lon, min_lat, max_lon, max_lat = bbox_tuple
        report_query = report_query.where(
            Report.longitude >= min_lon,
            Report.longitude <= max_lon,
            Report.latitude >= min_lat,
            Report.latitude <= max_lat,
        )

    result = await db.execute(report_query)
    reports = result.scalars().all()

    verified = sum(1 for r in reports if r.status == "verified")
    pending = sum(1 for r in reports if r.status == "submitted")

    # Count high risk cells in bbox
    risk_query = select(RiskCell).where(RiskCell.risk_band.in_(["high", "very_high"]))
    if bbox_tuple:
        min_lon, min_lat, max_lon, max_lat = bbox_tuple
        risk_query = risk_query.where(
            RiskCell.longitude >= min_lon,
            RiskCell.longitude <= max_lon,
            RiskCell.latitude >= min_lat,
            RiskCell.latitude <= max_lat,
        )
    risk_result = await db.execute(risk_query)
    high_risk = len(risk_result.scalars().all())

    return MapSummary(
        total_reports=len(reports),
        verified_incidents=verified,
        pending_reports=pending,
        high_risk_cells=high_risk,
        last_updated=datetime.now(timezone.utc),
        bbox=bbox or "-180,-90,180,90",
        is_seeded=True,
    )


@router.get("/reports", response_model=list[MapReportItem])
async def get_map_reports(
    bbox: str | None = Query(default=None),
    from_date: datetime | None = Query(default=None, alias="from"),
    to_date: datetime | None = Query(default=None, alias="to"),
    report_status: str | None = Query(default=None, alias="status"),
    hazard_type: str | None = Query(default=None, alias="hazard"),
    limit: int = Query(default=200, ge=1, le=1000),
    db: AsyncSession = Depends(get_async_session),
):
    """Get map report markers with filters."""
    query = select(Report).where(Report.status.in_(["submitted", "under_review", "verified"]))

    bbox_tuple = parse_bbox(bbox) if bbox else None
    if bbox_tuple:
        min_lon, min_lat, max_lon, max_lat = bbox_tuple
        query = query.where(
            Report.longitude >= min_lon,
            Report.longitude <= max_lon,
            Report.latitude >= min_lat,
            Report.latitude <= max_lat,
        )

    if from_date:
        query = query.where(Report.submitted_at >= from_date)
    if to_date:
        query = query.where(Report.submitted_at <= to_date)
    if report_status:
        query = query.where(Report.status == report_status)
    if hazard_type:
        query = query.where(Report.hazard_type == hazard_type)

    query = query.order_by(Report.submitted_at.desc()).limit(limit)

    result = await db.execute(query)
    reports = result.scalars().all()

    return [
        MapReportItem(
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
        )
        for r in reports
    ]


@router.get("/risk-cells", response_model=RiskCellList)
async def get_risk_cells(
    bbox: str | None = Query(default=None),
    band: str | None = Query(default=None, description="Filter by risk band"),
    limit: int = Query(default=200, ge=1, le=1000),
    db: AsyncSession = Depends(get_async_session),
):
    """Get risk cells for map display."""
    query = select(RiskCell)

    bbox_tuple = parse_bbox(bbox) if bbox else None
    if bbox_tuple:
        min_lon, min_lat, max_lon, max_lat = bbox_tuple
        query = query.where(
            RiskCell.longitude >= min_lon,
            RiskCell.longitude <= max_lon,
            RiskCell.latitude >= min_lat,
            RiskCell.latitude <= max_lat,
        )

    if band:
        query = query.where(RiskCell.risk_band == band)

    query = query.order_by(RiskCell.risk_score.desc()).limit(limit)

    result = await db.execute(query)
    cells = result.scalars().all()

    return RiskCellList(
        items=[
            RiskCellListItem(
                id=c.id,
                grid_index=c.grid_index,
                latitude=c.latitude,
                longitude=c.longitude,
                risk_score=c.risk_score,
                risk_band=c.risk_band,
                confidence_score=c.confidence_score,
                data_completeness=c.data_completeness,
                is_illustrative=c.is_illustrative,
                calculated_at=c.calculated_at,
            )
            for c in cells
        ],
        has_more=False,
    )


@router.get("/risk-cells/{cell_id}")
async def get_risk_cell_detail(
    cell_id: str,
    db: AsyncSession = Depends(get_async_session),
):
    """Get full detail of a single risk cell."""
    # Try as UUID first, then as grid index
    try:
        cell_uuid = __import__("uuid").UUID(cell_id)
        query = select(RiskCell).where(RiskCell.id == cell_uuid)
    except ValueError:
        query = select(RiskCell).where(RiskCell.grid_index == cell_id)

    result = await db.execute(query)
    cell = result.scalar_one_or_none()
    if cell is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Risk cell not found")

    from app.schemas.risk import RiskCellOut, ContributingFactor

    contributing = []
    if cell.contributing_factors:
        for f in cell.contributing_factors:
            if isinstance(f, dict):
                contributing.append(ContributingFactor(**f))
            else:
                contributing.append(ContributingFactor(
                    dimension=str(f), raw_value=0, weighted_score=0, max_weight=0
                ))

    return RiskCellOut(
        id=cell.id,
        grid_system=cell.grid_system,
        grid_index=cell.grid_index,
        latitude=cell.latitude,
        longitude=cell.longitude,
        risk_score=cell.risk_score,
        risk_band=cell.risk_band,
        confidence_score=cell.confidence_score,
        data_completeness=cell.data_completeness,
        contributing_factors=contributing,
        missing_inputs=cell.missing_inputs,
        source_ids=cell.source_ids,
        calculation_version=cell.calculation_version,
        calculated_at=cell.calculated_at,
        valid_until=cell.valid_until,
        is_illustrative=cell.is_illustrative,
    )


@router.get("/layers", response_model=list[LayerMetadata])
async def get_layers(
    db: AsyncSession = Depends(get_async_session),
):
    """Get layer metadata and freshness."""
    # Query data sources for layer info
    result = await db.execute(select(DataSource).order_by(DataSource.source_type))
    sources = result.scalars().all()

    layers = []
    for s in sources:
        layers.append(
            LayerMetadata(
                id=s.source_type,
                name=s.name,
                type=s.source_type,
                visible=True,
                source=s.source_url,
                last_updated=s.last_success_at,
                is_seeded=s.status in ("seeded", "demo"),
                attribution=s.attribution,
            )
        )

    # Ensure default layers exist even without data sources
    default_layers = [
        LayerMetadata(id="reports", name="Community Reports", type="markers", visible=True, is_seeded=True),
        LayerMetadata(id="risk-cells", name="Risk Zones", type="fill", visible=True, is_seeded=True),
    ]
    # Add defaults that aren't already in the list
    existing_ids = {l.id for l in layers}
    for dl in default_layers:
        if dl.id not in existing_ids:
            layers.append(dl)

    return layers
