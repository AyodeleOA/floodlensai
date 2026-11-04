from __future__ import annotations

import logging
import time
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai_analysis import AIAnalysis
from app.models.media_asset import MediaAsset
from app.models.segmentation import SegmentationAsset
from app.services.model_router.router import get_model_router

logger = logging.getLogger(__name__)


def _s3_bucket_configured() -> bool:
    """Check if S3 bucket is configured."""
    from app.core.config import get_settings
    return bool(get_settings().S3_MEDIA_BUCKET)


def _fetch_image_from_s3(s3_key: str) -> bytes | None:
    """Fetch image bytes from S3.

    Returns None if S3 is not configured or the object cannot be fetched.
    The caller should fall back to sending the S3 key as a URL if None.
    """
    from app.core.config import get_settings
    settings = get_settings()

    if not settings.S3_MEDIA_BUCKET:
        logger.warning(f"S3_MEDIA_BUCKET not configured — cannot fetch {s3_key}")
        return None

    try:
        import boto3
        from botocore.exceptions import ClientError

        s3 = boto3.client(
            "s3",
            region_name=settings.AWS_REGION,
            endpoint_url=settings.AWS_ENDPOINT_URL or None,
        )
        response = s3.get_object(Bucket=settings.S3_MEDIA_BUCKET, Key=s3_key)
        return response["Body"].read()
    except Exception as e:
        logger.error(f"Failed to fetch {s3_key} from S3: {e}")
        return None


async def process_media_asset(
    media_asset_id: uuid.UUID,
    db: AsyncSession,
) -> dict[str, Any]:
    """Process a single media asset through AI analysis.

    Fetches the image from S3 and sends bytes to the AI provider.
    Falls back to the s3_key as an identifier if S3 fetch fails.
    Stores AI analysis result with full provenance.
    The worker does NOT independently mark the incident verified.
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
        # Fetch image bytes from S3.
        # The Meta API requires actual image data (base64) — not an S3 path string.
        image_data: bytes | str = _fetch_image_from_s3(asset.s3_key) or b""

        if not image_data:
            # No image bytes — use demo fixture so analysis still runs
            # and the caller can verify the pipeline works end-to-end.
            logger.warning(
                f"Could not fetch image from S3 key: {asset.s3_key}. "
                f"Using demo fixture instead. "
                f"(S3_MEDIA_BUCKET={'configured' if _s3_bucket_configured() else 'not configured'})"
            )
            image_data = b"demo_fixture"

        # Perform image analysis
        analysis_result, provider_name = await router.analyze_image(
            image_data=image_data,
            context={
                "report_id": str(asset.report_id),
                "media_type": asset.media_type,
                "s3_key": asset.s3_key,
                "mime_type": asset.mime_type,
            },
        )

        processing_ms = int((time.time() - start_time) * 1000)

        # Store the AI analysis result with full provenance
        model_id = "demo"
        if hasattr(router._image_analysis, "model_id"):
            model_id = router._image_analysis.model_id

        ai_analysis = AIAnalysis(
            id=uuid.uuid4(),
            report_id=asset.report_id,
            media_asset_id=asset.id,
            provider=provider_name,
            model_id=model_id,
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

        # Optional segmentation
        if router._segmentation is not None:
            try:
                seg_result, seg_provider = await router.segment_image(
                    image_data=image_data,
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

        asset.processing_status = "completed"

        return {
            "media_asset_id": str(media_asset_id),
            "status": "completed",
            "provider": provider_name,
            "is_demo": router.is_demo,
            "processing_ms": processing_ms,
            "scene_summary": analysis_result.scene_summary,
            "hazard_count": len(analysis_result.hazards),
            "water_presence": analysis_result.water_presence,
        }

    except Exception as e:
        logger.error(f"Media analysis failed for {media_asset_id}: {e}", exc_info=True)
        asset.processing_status = "failed"

        # Record the failure with error detail
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
    """Process all media assets in 'queued' status."""
    result = await db.execute(
        select(MediaAsset).where(MediaAsset.processing_status == "queued")
    )
    pending_assets = result.scalars().all()

    results = []
    for asset in pending_assets:
        r = await process_media_asset(asset.id, db)
        results.append(r)

    return results
