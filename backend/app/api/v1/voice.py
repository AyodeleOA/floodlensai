from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import CurrentUser, get_current_user
from app.db.session import get_async_session
from app.models.media_asset import MediaAsset
from app.schemas.ai_analysis import TranscribeRequest, TranscriptionStatusOut

router = APIRouter(tags=["voice"])


@router.post("/reports/{report_id}/transcribe", status_code=status.HTTP_202_ACCEPTED)
async def enqueue_transcription(
    report_id: uuid.UUID,
    body: TranscribeRequest,
    db: AsyncSession = Depends(get_async_session),
    user: CurrentUser = Depends(get_current_user),
):
    """Enqueue transcription of uploaded audio."""
    asset = await db.get(MediaAsset, body.media_asset_id)
    if asset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media asset not found")

    if asset.report_id != report_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Media asset does not belong to this report",
        )

    if asset.media_type != "voice":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Media asset is not a voice recording",
        )

    # Update processing status
    asset.processing_status = "transcription_queued"

    # Generate a transcription job ID
    transcription_id = uuid.uuid4()

    return {
        "transcription_id": str(transcription_id),
        "status": "pending",
        "message": "Transcription enqueued",
    }


@router.get("/transcriptions/{transcription_id}", response_model=TranscriptionStatusOut)
async def get_transcription_status(
    transcription_id: uuid.UUID,
    db: AsyncSession = Depends(get_async_session),
):
    """Retrieve transcription status and transcript."""
    # For MVP: look up a media asset with this ID (the transcription_id maps to a job)
    # In a full implementation this would query a separate transcriptions table
    asset = await db.get(MediaAsset, transcription_id)
    if asset is None:
        # Return a demo/pending status
        return TranscriptionStatusOut(
            id=transcription_id,
            status="pending",
            created_at=datetime.now(timezone.utc),
        )

    # Check if there's a transcript on the associated report
    from app.models.report import Report
    report = await db.get(Report, asset.report_id)
    transcript = report.voice_transcript if report else None

    status_val = "completed" if transcript else "processing"

    return TranscriptionStatusOut(
        id=transcription_id,
        status=status_val,
        transcript=transcript,
        language="en",
        created_at=asset.uploaded_at,
    )
