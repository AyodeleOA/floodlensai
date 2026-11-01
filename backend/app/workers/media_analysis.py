from __future__ import annotations

import logging
import time
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai_analysis import AIAnalysis
from app.models.media_asset import MediaAsset
from app.models.report import Report
from app.models.segmentation import SegmentationAsset
from app.services.model_router.router import get_model_router

logger = logging.getLogger(__name__)


async def process_media_asset(
    media_asset_id: uuid.UUID,
    db: AsyncSession,
) -> dict[str, Any]:
    """Process a single media asset through AI analysis.

    This function is called by the SQS worker Lambda or can be run locally.
    It invokes the ModelRouter for image_assessment, optionally segmentation,
    and stores the results with full provenance.

    The worker computes preliminary evidence attributes but does NOT
    independently mark the incident verified.
    """
    start_time = time.time()

    # Load the media asset
    asset = await db.get(MediaAsset, media_asset_id)
    if asset is None:
        raise ValueError(f"Media asset {media_asset_id} not found")

    # Update processing status
    asset.processing_status = "processing"
    await db.flush()

    router = get_model_router()

    try:
        # Perform image analysis
        analysis_result, provider_name = await router.analyze_image(
            image_data=asset.s3_key,  # In production, fetch from S3
            context={
                "report_id": str(asset.report_id),
                "media_type": asset.media_type,
            },
        )

        processing_ms = int((time.time() - start_time) * 1000)

        # Store the AI analysis result with full provenance
        ai_analysis = AIAnalysis(
            id=uuid.uuid4(),
            report_id=asset.report_id,
            media_asset_id=asset.id,
            provider=provider_name,
            model_id=router._image_analysis.model_id if hasattr(router._image_analysis, "model_id") else "demo",
            model_version=None,
            prompt_version="muse_spark_v1",
            status="completed",
            scene_summary=analysis_result.scene_summary,
            structured_result=analysis_result.model_dump(),
            confidence=max((h.confidence for h in analysis_result.hazards), default=0.0),
            limitations=analysis_result.limitations,
            processing_ms=processing_ms,
        )
        db.add(ai_analysis)

        # Optional segmentation if enabled
        if router._segmentation is not None:
            try:
                seg_result, seg_provider = await router.segment_image(
                    image_data=asset.s3_key,
                    objects=["floodwater", "drain opening", "debris", "road surface"],
                )
                seg_asset = SegmentationAsset(
                    id=uuid.uuid4(),
                    media_asset_id=asset.id,
                    provider=seg_provider,
                    model_id=seg_result.get("model_id", "demo-sam"),
                    prompt_text="floodwater, drain opening, debris, road surface",
                    bounding_boxes=seg_result.get("bounding_boxes"),
                    object_labels=seg_result.get("object_labels"),
                )
                db.add(seg_asset)
            except Exception as e:
                logger.warning(f"Segmentation failed for {media_asset_id}: {e}")

        # Update media asset status
        asset.processing_status = "completed"

        return {
            "media_asset_id": str(media_asset_id),
            "status": "completed",
            "provider": provider_name,
            "processing_ms": processing_ms,
            "is_demo": router.is_demo,
        }

    except Exception as e:
        logger.error(f"Media analysis failed for {media_asset_id}: {e}")
        asset.processing_status = "failed"

        # Record the failure
        ai_analysis = AIAnalysis(
            id=uuid.uuid4(),
            report_id=asset.report_id,
            media_asset_id=asset.id,
            provider=router.provider_name,
            model_id="unknown",
            status="failed",
            scene_summary=None,
            structured_result=None,
            confidence=None,
            limitations=[f"Processing error: {str(e)[:500]}"],
            processing_ms=int((time.time() - start_time) * 1000),
        )
        db.add(ai_analysis)

        return {
            "media_asset_id": str(media_asset_id),
            "status": "failed",
            "error": str(e)[:500],
            "is_demo": router.is_demo,
        }


async def process_pending_media(db: AsyncSession) -> list[dict[str, Any]]:
    """Process all media assets in 'queued' status.

    Called by the worker Lambda or can be run locally for testing.
    """
    result = await db.execute(
        select(MediaAsset).where(MediaAsset.processing_status == "queued")
    )
    pending_assets = result.scalars().all()

    results = []
    for asset in pending_assets:
        r = await process_media_asset(asset.id, db)
        results.append(r)

    return results
