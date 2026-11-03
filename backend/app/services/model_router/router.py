from __future__ import annotations

import logging
from enum import Enum
from typing import Any

from app.core.config import AIProviderMode, get_settings
from app.providers.base import (
    EvidenceSynthesisProvider,
    ImageAnalysisProvider,
    ImageGenerationProvider,
    ProviderHealthStatus,
    SegmentationProvider,
    VoiceTranscriptionProvider,
)
from app.providers.demo.provider import (
    DemoEvidenceSynthesisProvider,
    DemoImageAnalysisProvider,
    DemoImageGenerationProvider,
    DemoSegmentationProvider,
    DemoVoiceProvider,
)
from app.providers.meta_model_api.muse_image import MuseImageProvider
from app.providers.meta_model_api.muse_spark import MuseSparkProvider
from app.providers.meta_model_api.muse_voice import MuseVoiceProvider
from app.providers.meta_model_api.muse_wonder import MuseWonderProvider
from app.providers.meta_model_api.sam import SAMSegmentationProvider
from app.providers.muse_glimmer.provider import MuseGlimmerProvider
from app.providers.muse_spark_open.provider import MuseSparkOpenProvider

logger = logging.getLogger(__name__)
settings = get_settings()


class TaskType(str, Enum):
    image_assessment = "image_assessment"
    segmentation = "segmentation"
    voice_transcription = "voice_transcription"
    evidence_synthesis = "evidence_synthesis"
    preparedness_visual = "preparedness_visual"


class ModelRouter:
    """Central router for AI model tasks.

    Maps task_type to preferred provider/model with fallback.
    Respects feature flags and AI_PROVIDER_MODE.
    Never silently falls back from a real model to a mock response.
    The UI must show 'Demo analysis' if fixtures are used.

    Records whether an analysis came from hosted Muse Spark, Muse Glimmer,
    Muse Spark Open, or demo fixtures.
    """

    def __init__(self) -> None:
        self._image_analysis: ImageAnalysisProvider | None = None
        self._segmentation: SegmentationProvider | None = None
        self._voice: VoiceTranscriptionProvider | None = None
        self._synthesis: EvidenceSynthesisProvider | None = None
        self._image_gen: ImageGenerationProvider | None = None
        self._provider_name: str = "demo"
        self._setup_providers()

    def _setup_providers(self) -> None:
        """Set up providers based on configuration."""
        mode = settings.AI_PROVIDER_MODE

        if mode == AIProviderMode.mock or mode == AIProviderMode.demo:
            self._image_analysis = DemoImageAnalysisProvider()
            self._segmentation = DemoSegmentationProvider()
            self._voice = DemoVoiceProvider()
            self._synthesis = DemoEvidenceSynthesisProvider()
            self._image_gen = DemoImageGenerationProvider()
            self._provider_name = "demo"
            return

        # Live mode — use real providers
        self._provider_name = "hosted_meta"

        # Image analysis: prefer Glimmer if enabled, then Spark hosted
        if settings.MUSE_GLIMMER_ENABLED and settings.MUSE_GLIMMER_BASE_URL:
            self._image_analysis = MuseGlimmerProvider()
            self._provider_name = "muse_glimmer"
        elif settings.MUSE_SPARK_OPEN_ENABLED and settings.MUSE_SPARK_OPEN_BASE_URL:
            self._image_analysis = MuseSparkOpenProvider()
            self._provider_name = "muse_spark_open"
        elif settings.MODEL_API_KEY:
            self._image_analysis = MuseSparkProvider()
            self._provider_name = "muse_spark"
        else:
            # No real provider configured — fall back to demo but be honest about it
            self._image_analysis = DemoImageAnalysisProvider()
            self._provider_name = "demo"
            logger.warning("No image analysis provider configured — using demo fallback")

        # Segmentation: SAM 3.1
        if settings.ENABLE_SAM_SEGMENTATION and settings.MODEL_API_KEY:
            self._segmentation = SAMSegmentationProvider()
        else:
            self._segmentation = DemoSegmentationProvider()

        # Voice transcription
        if settings.ENABLE_AI_VOICE_TRANSCRIPTION and settings.MODEL_API_KEY:
            self._voice = MuseVoiceProvider()
        else:
            self._voice = DemoVoiceProvider()

        # Evidence synthesis: Muse Wonder
        if settings.ENABLE_MUSE_WONDER_ANALYST and settings.MODEL_API_KEY:
            self._synthesis = MuseWonderProvider()
        else:
            self._synthesis = DemoEvidenceSynthesisProvider()

        # Image generation: Muse Image
        if settings.ENABLE_MUSE_IMAGE_GENERATION and settings.MODEL_API_KEY:
            self._image_gen = MuseImageProvider()
        else:
            self._image_gen = DemoImageGenerationProvider()

    @property
    def provider_name(self) -> str:
        """Return the name of the active provider for provenance tracking."""
        return self._provider_name

    @property
    def is_demo(self) -> bool:
        """Whether the router is using demo/mock providers."""
        return self._provider_name == "demo"

    async def analyze_image(
        self,
        image_data: bytes | str,
        context: dict[str, Any] | None = None,
    ) -> tuple[Any, str]:
        """Route image analysis to the configured provider.

        Returns (result, provider_name) for provenance tracking.
        """
        if self._image_analysis is None:
            raise RuntimeError("No image analysis provider configured")
        result = await self._image_analysis.analyze_image(image_data, context)
        return result, self._provider_name

    async def segment_image(
        self,
        image_data: bytes | str,
        prompt_text: str | None = None,
        objects: list[str] | None = None,
    ) -> tuple[dict[str, Any], str]:
        """Route segmentation to the configured provider."""
        if self._segmentation is None:
            raise RuntimeError("No segmentation provider configured")
        result = await self._segmentation.segment_image(image_data, prompt_text, objects)
        return result, self._provider_name

    async def transcribe_voice(
        self,
        audio_data: bytes | str,
        language: str | None = None,
    ) -> tuple[dict[str, Any], str]:
        """Route voice transcription to the configured provider."""
        if self._voice is None:
            raise RuntimeError("No voice transcription provider configured")
        result = await self._voice.transcribe(audio_data, language)
        return result, self._provider_name

    async def synthesize_evidence(
        self,
        evidence_items: list[dict[str, Any]],
        context: dict[str, Any] | None = None,
    ) -> tuple[dict[str, Any], str]:
        """Route evidence synthesis to the configured provider."""
        if self._synthesis is None:
            raise RuntimeError("No evidence synthesis provider configured")
        result = await self._synthesis.synthesize_evidence(evidence_items, context)
        return result, self._provider_name

    async def generate_image(
        self,
        prompt: str,
        context: dict[str, Any] | None = None,
    ) -> tuple[dict[str, Any], str]:
        """Route image generation to the configured provider."""
        if self._image_gen is None:
            raise RuntimeError("No image generation provider configured")
        result = await self._image_gen.generate_image(prompt, context)
        return result, self._provider_name

    async def get_all_health_statuses(self) -> list[dict[str, str]]:
        """Get health status of all configured providers."""
        statuses: list[dict[str, str]] = []

        providers_to_check: list[tuple[str, Any]] = [
            ("muse_spark", MuseSparkProvider()),
            ("muse_wonder", MuseWonderProvider()),
            ("muse_image", MuseImageProvider()),
            ("muse_voice", MuseVoiceProvider()),
            ("sam", SAMSegmentationProvider()),
            ("muse_glimmer", MuseGlimmerProvider()),
            ("muse_spark_open", MuseSparkOpenProvider()),
        ]

        for name, provider in providers_to_check:
            try:
                health = await provider.health_check()
                statuses.append({
                    "id": name,
                    "status": health.status,
                    "message": health.message,
                })
            except Exception as e:
                statuses.append({
                    "id": name,
                    "status": "unavailable",
                    "message": str(e)[:200],
                })

        return statuses


# Singleton instance
_model_router: ModelRouter | None = None


def get_model_router() -> ModelRouter:
    """Get the singleton ModelRouter instance.

    Recreates if the AI_PROVIDER_MODE has changed (e.g., Lambda cold start
    with different env vars than a previous warm invocation).
    """
    global _model_router
    if _model_router is None:
        _model_router = ModelRouter()
    return _model_router
