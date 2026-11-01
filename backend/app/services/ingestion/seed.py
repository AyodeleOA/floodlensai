from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.data_source import DataSource
from app.models.report import Report
from app.models.risk_cell import RiskCell
from app.services.geospatial.grid import assign_to_grid_cell, get_cell_center
from app.services.risk_engine.engine import RiskEngine

# Lagos, Nigeria center coordinates
LAGOS_CENTER = (6.4541, 3.3947)

# Synthetic report locations around Lagos
SYNTHETIC_REPORTS = [
    {
        "report_type": "flooding",
        "hazard_type": "floodwater",
        "severity": "high",
        "latitude": 6.4474,
        "longitude": 3.4084,
        "description": "Heavy flooding on Lagos Island after overnight rain. Water entering ground floor shops.",
        "landmark": "Near Lagos Island roundabout",
        "water_level": "knee",
        "affects_roads": True,
        "affects_homes": True,
        "affects_shops": True,
        "days_ago": 2,
    },
    {
        "report_type": "drainage",
        "hazard_type": "blocked_drain",
        "severity": "moderate",
        "latitude": 6.6018,
        "longitude": 3.3515,
        "description": "Main drainage channel blocked by debris near Ikorodu Road. Water backing up.",
        "landmark": "Ikorodu Road, near Mile 12",
        "water_level": "ankle",
        "affects_roads": True,
        "days_ago": 3,
    },
    {
        "report_type": "flooding",
        "hazard_type": "floodwater",
        "severity": "critical",
        "latitude": 6.5095,
        "longitude": 3.3714,
        "description": "Severe flooding in Agege area. Multiple streets impassable. Residents trapped.",
        "landmark": "Agege, Pen-Cinema area",
        "water_level": "waist",
        "affects_roads": True,
        "affects_homes": True,
        "affects_facilities": True,
        "days_ago": 1,
    },
    {
        "report_type": "road_damage",
        "hazard_type": "damaged_road",
        "severity": "moderate",
        "latitude": 6.4330,
        "longitude": 3.4210,
        "description": "Road surface damaged by floodwater erosion on Victoria Island.",
        "landmark": "Victoria Island, Adeola Odeku Street",
        "affects_roads": True,
        "days_ago": 4,
    },
    {
        "report_type": "flooding",
        "hazard_type": "floodwater",
        "severity": "high",
        "latitude": 6.5244,
        "longitude": 3.3792,
        "description": "Extensive flooding in Surulere after 6 hours of continuous rain.",
        "landmark": "Surulere, Adeniran Ogunsanya",
        "water_level": "knee",
        "affects_roads": True,
        "affects_homes": True,
        "days_ago": 1,
    },
    {
        "report_type": "drainage",
        "hazard_type": "overflowing_drain",
        "severity": "high",
        "latitude": 6.4650,
        "longitude": 3.6230,
        "description": "Drainage overflow at Lekki Phase 1. Water covering the main access road.",
        "landmark": "Lekki Phase 1, by the main gate",
        "affects_roads": True,
        "affects_shops": True,
        "days_ago": 2,
    },
    {
        "report_type": "flooding",
        "hazard_type": "floodwater",
        "severity": "moderate",
        "latitude": 6.6000,
        "longitude": 3.3500,
        "description": "Floodwater receding in Ikeja but roads still waterlogged.",
        "landmark": "Ikeja, Allen Avenue",
        "water_level": "ankle",
        "affects_roads": True,
        "days_ago": 3,
    },
    {
        "report_type": "flooding",
        "hazard_type": "floodwater",
        "severity": "high",
        "latitude": 6.4400,
        "longitude": 3.4000,
        "description": "Apapa area flooded. Trucks stuck. Port access limited.",
        "landmark": "Apapa, near Tin Can Island",
        "water_level": "knee",
        "affects_roads": True,
        "affects_shops": True,
        "affects_facilities": True,
        "days_ago": 1,
    },
    {
        "report_type": "drainage",
        "hazard_type": "blocked_drain",
        "severity": "moderate",
        "latitude": 6.5550,
        "longitude": 3.3900,
        "description": "Drain blocked by construction waste in Ogba. Water not draining after rain.",
        "landmark": "Ogba, by the market",
        "affects_roads": True,
        "affects_shops": True,
        "days_ago": 5,
    },
    {
        "report_type": "flooding",
        "hazard_type": "exposed_infrastructure",
        "severity": "high",
        "latitude": 6.5200,
        "longitude": 3.3800,
        "description": "Floodwater exposing electrical infrastructure near Yaba. Safety hazard.",
        "landmark": "Yaba, near the railway crossing",
        "affects_roads": True,
        "affects_facilities": True,
        "days_ago": 2,
    },
    {
        "report_type": "flooding",
        "hazard_type": "floodwater",
        "severity": "moderate",
        "latitude": 6.5800,
        "longitude": 3.3400,
        "description": "Waterlogged streets in Ifako-Ijaiye after heavy downpour.",
        "landmark": "Ifako-Ijaiye, Iju Road",
        "water_level": "ankle",
        "affects_roads": True,
        "days_ago": 4,
    },
    {
        "report_type": "flooding",
        "hazard_type": "floodwater",
        "severity": "very_high",
        "latitude": 6.4700,
        "longitude": 3.3800,
        "description": "Critical flooding in Mushin. Multiple homes affected. Urgent assistance needed.",
        "landmark": "Mushin, Ojuwoye market area",
        "water_level": "above_waist",
        "affects_roads": True,
        "affects_homes": True,
        "affects_shops": True,
        "days_ago": 1,
    },
    {
        "report_type": "drainage",
        "hazard_type": "blocked_drain",
        "severity": "low",
        "latitude": 6.5300,
        "longitude": 3.4300,
        "description": "Minor drain blockage reported in Somolu. Monitoring situation.",
        "landmark": "Somolu, Bariga Road",
        "days_ago": 6,
    },
    {
        "report_type": "flooding",
        "hazard_type": "floodwater",
        "severity": "moderate",
        "latitude": 6.6100,
        "longitude": 3.3600,
        "description": "Floodwater on Ojota expressway. Traffic severely affected.",
        "landmark": "Ojota, by the expressway",
        "water_level": "ankle",
        "affects_roads": True,
        "days_ago": 3,
    },
    {
        "report_type": "flooding",
        "hazard_type": "floodwater",
        "severity": "high",
        "latitude": 6.4900,
        "longitude": 3.3600,
        "description": "Flooding in Shomolu. Several streets under water.",
        "landmark": "Shomolu, Bajulaiye Road",
        "water_level": "knee",
        "affects_roads": True,
        "affects_homes": True,
        "days_ago": 2,
    },
    {
        "report_type": "road_damage",
        "hazard_type": "damaged_road",
        "severity": "low",
        "latitude": 6.5700,
        "longitude": 3.3700,
        "description": "Potholes forming after floodwater receded in Ojodu.",
        "landmark": "Ojodu Berger",
        "affects_roads": True,
        "days_ago": 5,
    },
    {
        "report_type": "flooding",
        "hazard_type": "floodwater",
        "severity": "moderate",
        "latitude": 6.4300,
        "longitude": 3.4300,
        "description": "Water receding in Eti-Osa but ground still saturated.",
        "landmark": "Eti-Osa, Ikoyi",
        "water_level": "ankle",
        "days_ago": 4,
    },
    {
        "report_type": "flooding",
        "hazard_type": "floodwater",
        "severity": "high",
        "latitude": 6.5000,
        "longitude": 3.3500,
        "description": "Major flooding reported in Oshodi. Market area affected.",
        "landmark": "Oshodi market",
        "water_level": "knee",
        "affects_roads": True,
        "affects_shops": True,
        "days_ago": 1,
    },
]


# Synthetic data sources
SYNTHETIC_DATA_SOURCES = [
    {
        "name": "NASA GPM IMERG Rainfall",
        "source_type": "rainfall",
        "licence": "Public Domain",
        "attribution": "NASA GPM IMERG",
        "source_url": "https://gpm.nasa.gov/data",
        "spatial_coverage": "Lagos, Nigeria (demo)",
        "temporal_coverage": "2024-06 to 2024-10",
        "update_frequency": "30 min",
        "status": "seeded",
        "limitations": "Synthetic data for demonstration. Not live rainfall readings.",
    },
    {
        "name": "Copernicus DEM Elevation",
        "source_type": "elevation",
        "licence": "Copernicus Programme",
        "attribution": "Copernicus DEM",
        "source_url": "https://spacedata.copernicus.eu/",
        "spatial_coverage": "Lagos, Nigeria (demo)",
        "temporal_coverage": "2021",
        "update_frequency": "N/A",
        "status": "seeded",
        "limitations": "Synthetic elevation data for demonstration.",
    },
    {
        "name": "OpenStreetMap Drainage",
        "source_type": "drainage",
        "licence": "ODbL",
        "attribution": "OpenStreetMap contributors",
        "source_url": "https://www.openstreetmap.org/",
        "spatial_coverage": "Lagos, Nigeria (partial)",
        "temporal_coverage": "Extracted 2024",
        "update_frequency": "Continuous",
        "status": "seeded",
        "limitations": "OSM drainage coverage may be incomplete in some areas.",
    },
    {
        "name": "OpenStreetMap Roads",
        "source_type": "roads",
        "licence": "ODbL",
        "attribution": "OpenStreetMap contributors",
        "source_url": "https://www.openstreetmap.org/",
        "spatial_coverage": "Lagos, Nigeria",
        "temporal_coverage": "Extracted 2024",
        "update_frequency": "Continuous",
        "status": "seeded",
    },
    {
        "name": "OpenStreetMap Waterways",
        "source_type": "waterways",
        "licence": "ODbL",
        "attribution": "OpenStreetMap contributors",
        "source_url": "https://www.openstreetmap.org/",
        "spatial_coverage": "Lagos, Nigeria",
        "temporal_coverage": "Extracted 2024",
        "update_frequency": "Continuous",
        "status": "seeded",
    },
    {
        "name": "Lagos Facilities Registry",
        "source_type": "facilities",
        "licence": "Open Government Data",
        "attribution": "Lagos State Government",
        "source_url": "",
        "spatial_coverage": "Lagos, Nigeria (demo)",
        "temporal_coverage": "2024",
        "update_frequency": "Annual",
        "status": "seeded",
        "limitations": "Synthetic facility data for demonstration.",
    },
]


async def seed_demo_data(db: AsyncSession) -> dict[str, int]:
    """Seed the database with synthetic demo data for Lagos, Nigeria.

    All data is clearly labelled is_synthetic=True / is_illustrative=True.
    """
    # Check if already seeded
    existing = await db.execute(select(Report).where(Report.is_synthetic).limit(1))
    if existing.scalar_one_or_none() is not None:
        return {"reports": 0, "risk_cells": 0, "data_sources": 0}

    # --- Data sources ---
    source_map: dict[str, uuid.UUID] = {}
    for src_data in SYNTHETIC_DATA_SOURCES:
        ds = DataSource(
            id=uuid.uuid4(),
            **src_data,
            last_success_at=datetime.now(timezone.utc),
        )
        db.add(ds)
        source_map[src_data["source_type"]] = ds.id

    # --- Reports ---
    report_map: dict[str, uuid.UUID] = {}
    for i, r_data in enumerate(SYNTHETIC_REPORTS):
        days_ago = r_data.pop("days_ago")
        reported_at = datetime.now(timezone.utc) - timedelta(days=days_ago)
        status_val = "verified" if i % 3 == 0 else ("under_review" if i % 3 == 1 else "submitted")

        report = Report(
            id=uuid.uuid4(),
            report_type=r_data["report_type"],
            hazard_type=r_data.get("hazard_type"),
            severity=r_data.get("severity"),
            latitude=r_data["latitude"],
            longitude=r_data["longitude"],
            description=r_data.get("description"),
            landmark=r_data.get("landmark"),
            water_level=r_data.get("water_level"),
            affects_roads=r_data.get("affects_roads"),
            affects_homes=r_data.get("affects_homes"),
            affects_shops=r_data.get("affects_shops"),
            affects_facilities=r_data.get("affects_facilities"),
            reported_at=reported_at,
            submitted_at=reported_at,
            status=status_val,
            source_channel="web",
            is_synthetic=True,
            privacy_consent=True,
        )
        db.add(report)
        report_map[f"report_{i}"] = report.id

    # --- Risk cells ---
    engine = RiskEngine("illustrative_unvalidated")
    risk_cell_count = 0
    seen_cells: set[str] = set()

    for r_data in SYNTHETIC_REPORTS:
        cell_index = assign_to_grid_cell(r_data["latitude"], r_data["longitude"], resolution=8)
        if cell_index in seen_cells:
            continue
        seen_cells.add(cell_index)

        cell_lat, cell_lng = get_cell_center(cell_index)

        # Build synthetic risk dimension values from report data
        severity_scores = {"low": 0.2, "moderate": 0.4, "high": 0.7, "critical": 0.95, "very_high": 0.95}
        sev = r_data.get("severity", "moderate")
        observed = severity_scores.get(sev, 0.4)

        result = engine.calculate_from_values(
            observed_flooding=observed,
            rainfall_conditions=0.6,
            terrain_susceptibility=0.45,
            drainage_condition=0.3 if r_data.get("hazard_type") == "blocked_drain" else 0.5,
            exposure_vulnerability=0.55,
        )

        valid_until = datetime.now(timezone.utc) + timedelta(hours=24)
        risk_cell = RiskCell(
            id=uuid.uuid4(),
            grid_system="h3",
            grid_index=cell_index,
            latitude=cell_lat,
            longitude=cell_lng,
            risk_score=result.risk_score,
            risk_band=result.risk_band,
            confidence_score=result.confidence_score,
            data_completeness=result.data_completeness,
            contributing_factors=result.contributing_factors,
            missing_inputs=result.missing_inputs,
            source_ids=[str(report_map[f"report_{SYNTHETIC_REPORTS.index(r_data)}"])],
            calculation_version=result.calculation_version,
            calculated_at=result.calculated_at,
            valid_until=valid_until,
            is_illustrative=True,
        )
        db.add(risk_cell)
        risk_cell_count += 1

    return {
        "reports": len(SYNTHETIC_REPORTS),
        "risk_cells": risk_cell_count,
        "data_sources": len(SYNTHETIC_DATA_SOURCES),
    }
