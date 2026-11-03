from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.session import get_async_session
from app.schemas.common import Disclaimer
from app.schemas.system import SystemCapabilities

router = APIRouter(prefix="/system", tags=["system"])
settings = get_settings()


@router.get("/capabilities", response_model=SystemCapabilities)
async def get_capabilities(
    db: AsyncSession = Depends(get_async_session),
):
    """Safe frontend feature flags, provider status, and enabled layers. Never returns secrets."""
    features = {
        "ai_image_analysis": settings.ENABLE_AI_IMAGE_ANALYSIS,
        "ai_voice_transcription": settings.ENABLE_AI_VOICE_TRANSCRIPTION,
        "sam_segmentation": settings.ENABLE_SAM_SEGMENTATION,
        "muse_image_generation": settings.ENABLE_MUSE_IMAGE_GENERATION,
        "muse_wonder_analyst": settings.ENABLE_MUSE_WONDER_ANALYST,
        "muse_glimmer": settings.MUSE_GLIMMER_ENABLED,
        "muse_spark_open": settings.MUSE_SPARK_OPEN_ENABLED,
        "demo_mode": settings.DEMO_MODE,
        "offline_drafts": True,
        "voice_reporting": settings.ENABLE_AI_VOICE_TRANSCRIPTION,
    }

    enabled_layers = [
        "reports",
        "risk-cells",
        "rainfall" if settings.DEMO_MODE else "rainfall",
        "elevation",
        "drainage",
        "roads",
        "waterways",
        "facilities",
    ]

    is_mock = settings.AI_PROVIDER_MODE.value in ("mock", "demo")
    is_live = settings.AI_PROVIDER_MODE.value == "live" and bool(settings.MODEL_API_KEY)
    # When in live mode but no feature flags enabled, the ModelRouter still
    # falls back to demo providers — so show "demo_mode" in that case.
    effective_demo = is_mock or (not is_live) or settings.DEMO_MODE

    def model_status(feature_enabled: bool) -> str:
        if is_live and feature_enabled:
            return "connected"
        if effective_demo:
            return "demo_mode"
        return "not_configured"

    model_statuses = [
        {"id": "muse_spark", "status": model_status(settings.ENABLE_AI_IMAGE_ANALYSIS)},
        {"id": "muse_voice", "status": model_status(settings.ENABLE_AI_VOICE_TRANSCRIPTION)},
        {"id": "sam", "status": model_status(settings.ENABLE_SAM_SEGMENTATION)},
        {"id": "muse_image", "status": model_status(settings.ENABLE_MUSE_IMAGE_GENERATION)},
        {"id": "muse_wonder", "status": model_status(settings.ENABLE_MUSE_WONDER_ANALYST)},
        {"id": "muse_glimmer", "status": "connected" if settings.MUSE_GLIMMER_ENABLED and settings.MUSE_GLIMMER_BASE_URL else "not_configured"},
        {"id": "muse_spark_open", "status": "connected" if settings.MUSE_SPARK_OPEN_ENABLED and settings.MUSE_SPARK_OPEN_BASE_URL else "not_configured"},
    ]

    return SystemCapabilities(
        app_name=settings.APP_NAME,
        app_env=settings.APP_ENV.value,
        demo_mode=settings.DEMO_MODE,
        ai_provider_mode=settings.AI_PROVIDER_MODE.value,
        features=features,
        enabled_layers=enabled_layers,
        model_statuses=model_statuses,
        disclaimer=Disclaimer(),
        api_version="v1",
    )
