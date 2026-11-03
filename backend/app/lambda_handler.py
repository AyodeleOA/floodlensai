from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import Any
from urllib.parse import unquote

from mangum import Mangum

from app.main import app

logger = logging.getLogger(__name__)

# Mangum handler — we use api_gateway_base_path="" (empty, default) and
# strip the stage prefix ourselves in the handler wrapper below.
# This is more reliable than depending on Mangum's internal stripping.
_mangum_handler = Mangum(app, lifespan="off")


def _strip_stage_from_event(event: dict[str, Any]) -> dict[str, Any]:
    """Strip the API Gateway stage prefix from the event's rawPath.

    API Gateway HTTP API v2 events include the stage name in rawPath:
        rawPath: /prod/api/v1/system/capabilities
    But FastAPI routes don't include the stage:
        route: /api/v1/system/capabilities

    We also need to fix requestContext.http.path if present.
    """
    stage = event.get("requestContext", {}).get("stage", "")
    if not stage or stage == "$default":
        return event

    stage_prefix = f"/{stage}"

    # Fix rawPath
    raw_path = event.get("rawPath", "")
    if raw_path.startswith(stage_prefix + "/"):
        event["rawPath"] = raw_path[len(stage_prefix):]
    elif raw_path == stage_prefix:
        event["rawPath"] = "/"

    # Fix requestContext.http.path (used by some Mangum versions)
    http_ctx = event.get("requestContext", {}).get("http", {})
    if http_ctx:
        http_path = http_ctx.get("path", "")
        if http_path.startswith(stage_prefix + "/"):
            http_ctx["path"] = http_path[len(stage_prefix):]
        elif http_path == stage_prefix:
            http_ctx["path"] = "/"

    return event


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """API Gateway handler for the FastAPI app.

    Strips the API Gateway stage prefix from the event before passing
    to Mangum so FastAPI routes match correctly.
    """
    event = _strip_stage_from_event(event)
    return _mangum_handler(event, context)


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
