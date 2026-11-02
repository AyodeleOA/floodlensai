from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from mangum import Mangum

from app.main import app

logger = logging.getLogger(__name__)

# Mangum adapter wrapping the FastAPI app for AWS Lambda (API Gateway)
handler = Mangum(app, lifespan="off")


def sqs_worker_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """SQS-triggered Lambda handler for media analysis jobs.

    Each SQS record contains a media_asset_id to process.
    This handler is separate from the API Gateway handler.
    """
    from app.db.session import get_session_context
    from app.workers.media_analysis import process_media_asset

    records = event.get("Records", [])
    results = []

    for record in records:
        try:
            body = json.loads(record["body"])
            media_asset_id_str = body.get("media_asset_id")
            if not media_asset_id_str:
                logger.warning("SQS record missing media_asset_id")
                results.append({"status": "skipped", "reason": "missing media_asset_id"})
                continue

            import uuid
            media_asset_id = uuid.UUID(media_asset_id_str)

            async def _process() -> dict[str, Any]:
                async with get_session_context() as db:
                    return await process_media_asset(media_asset_id, db)

            result = asyncio.run(_process())
            results.append(result)
        except Exception as e:
            logger.error(f"Worker error processing record: {e}")
            results.append({"status": "failed", "error": str(e)[:500]})

    return {"batchItemFailures": [], "results": results}
