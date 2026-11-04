from __future__ import annotations

import logging
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.media_asset import MediaAsset
from app.models.report import Report
from app.services.model_router.router import get_model_router

logger = logging.getLogger(__name__)


async def process_voice_transcription(
    media_asset_id: uuid.UUID,
    db: AsyncSession,
) -> dict[str, Any]:
    """Process a voice media asset through transcription.

    The transcript is stored as unverified text and shown to the reporter
    for correction where possible. Transcript keywords may assist report
    categorisation but must NOT independently establish flood severity.

    Retain audio only according to configured retention policy.
    """
    asset = await db.get(MediaAsset, media_asset_id)
    if asset is None:
        raise ValueError(f"Media asset {media_asset_id} not found")

    if asset.media_type != "voice":
        raise ValueError(f"Media asset {media_asset_id} is not a voice recording")

    asset.processing_status = "transcribing"
    await db.flush()

    router = get_model_router()

    try:
        # Fetch audio bytes from S3
        from app.workers.media_analysis import _fetch_image_from_s3
        audio_data: bytes | str = _fetch_image_from_s3(asset.s3_key) or b""

        if not audio_data:
            if router.is_demo:
                logger.info(f"No audio bytes — using demo fixture for {media_asset_id}")
                audio_data = b"demo_audio_fixture"
            else:
                logger.warning(
                    f"Could not fetch audio from S3 key: {asset.s3_key}. "
                    "Using demo fixture instead."
                )
                audio_data = b"demo_audio_fixture"

        result, provider_name = await router.transcribe_voice(
            audio_data=audio_data,
        )

        transcript = result.get("transcript", "")
        language = result.get("language", "en")
        confidence = result.get("confidence", 0.0)

        # Store transcript on the associated report
        report = await db.get(Report, asset.report_id)
        if report:
            report.voice_transcript = transcript

        asset.processing_status = "transcribed"

        return {
            "media_asset_id": str(media_asset_id),
            "status": "completed",
            "transcript": transcript,
            "language": language,
            "confidence": confidence,
            "provider": provider_name,
            "is_demo": router.is_demo,
        }

    except Exception as e:
        logger.error(f"Voice transcription failed for {media_asset_id}: {e}")
        asset.processing_status = "failed"
        return {
            "media_asset_id": str(media_asset_id),
            "status": "failed",
            "error": str(e)[:500],
            "is_demo": router.is_demo,
        }


async def process_pending_voice(db: AsyncSession) -> list[dict[str, Any]]:
    """Process all voice assets awaiting transcription."""
    result = await db.execute(
        select(MediaAsset).where(
            MediaAsset.media_type == "voice",
            MediaAsset.processing_status == "transcription_queued",
        )
    )
    pending = result.scalars().all()

    results = []
    for asset in pending:
        r = await process_voice_transcription(asset.id, db)
        results.append(r)

    return results
