from __future__ import annotations

import abc
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from app.schemas.ai_analysis import MuseSparkAnalysisResult


@dataclass
class ProviderHealthStatus:
    """Health status of a provider adapter."""

    status: str  # connected, not_configured, unavailable, demo_mode
    message: str = ""
    last_check: datetime | None = None
    endpoint: str | None = None


class ImageAnalysisProvider(abc.ABC):
    """Abstract interface for image analysis providers (Muse Spark, Glimmer, etc.)."""

    @abc.abstractmethod
    async def analyze_image(
        self,
        image_data: bytes | str,
        context: dict[str, Any] | None = None,
    ) -> MuseSparkAnalysisResult:
        """Analyze an image and return structured observations.

        Args:
            image_data: Raw image bytes or S3 key/URL.
            context: Optional metadata about the report location, time, etc.

        Returns:
            Normalised analysis result matching the internal schema.
        """
        ...

    @abc.abstractmethod
    async def health_check(self) -> ProviderHealthStatus:
        """Check if the provider is available and configured."""
        ...


class SegmentationProvider(abc.ABC):
    """Abstract interface for segmentation providers (SAM 3.1, etc.)."""

    @abc.abstractmethod
    async def segment_image(
        self,
        image_data: bytes | str,
        prompt_text: str | None = None,
        objects: list[str] | None = None,
    ) -> dict[str, Any]:
        """Segment objects/regions in an image.

        Args:
            image_data: Raw image bytes or S3 key/URL.
            prompt_text: Optional text prompt for targeted segmentation.
            objects: List of object names to look for (floodwater, drain, debris, etc.).

        Returns:
            Dict with masks, bounding_boxes, and object_labels.
        """
        ...

    @abc.abstractmethod
    async def health_check(self) -> ProviderHealthStatus:
        """Check if the provider is available and configured."""
        ...


class VoiceTranscriptionProvider(abc.ABC):
    """Abstract interface for voice-to-text providers (Muse Voice, etc.)."""

    @abc.abstractmethod
    async def transcribe(
        self,
        audio_data: bytes | str,
        language: str | None = None,
    ) -> dict[str, Any]:
        """Transcribe audio to text.

        Args:
            audio_data: Raw audio bytes or S3 key/URL.
            language: Optional language hint.

        Returns:
            Dict with transcript, language, confidence, duration_ms, timestamps.
        """
        ...

    @abc.abstractmethod
    async def health_check(self) -> ProviderHealthStatus:
        """Check if the provider is available and configured."""
        ...


class EvidenceSynthesisProvider(abc.ABC):
    """Abstract interface for evidence synthesis providers (Muse Wonder, etc.)."""

    @abc.abstractmethod
    async def synthesize_evidence(
        self,
        evidence_items: list[dict[str, Any]],
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Synthesize multiple evidence items into a coherent assessment.

        Args:
            evidence_items: List of evidence dicts (reports, AI analyses, environmental data).
            context: Optional context about the hotspot or area.

        Returns:
            Dict with summary, uncertainty, source_report_ids, missing_conflicting_evidence.
        """
        ...

    @abc.abstractmethod
    async def health_check(self) -> ProviderHealthStatus:
        """Check if the provider is available and configured."""
        ...


class ImageGenerationProvider(abc.ABC):
    """Abstract interface for image generation providers (Muse Image, etc.)."""

    @abc.abstractmethod
    async def generate_image(
        self,
        prompt: str,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Generate a preparedness illustration or demo asset.

        Args:
            prompt: Text description of the image to generate.
            context: Optional metadata.

        Returns:
            Dict with image data/URL, watermark label, and metadata.
        """
        ...

    @abc.abstractmethod
    async def health_check(self) -> ProviderHealthStatus:
        """Check if the provider is available and configured."""
        ...


class OpenWeightInferenceProvider(abc.ABC):
    """Abstract interface for open-weight inference adapters.

    These adapters call an OpenAI-compatible private endpoint.
    They do not load model weights directly into the application.
    """

    @abc.abstractmethod
    async def chat_completion(
        self,
        messages: list[dict[str, str]],
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Send a chat completion request to the OpenAI-compatible endpoint.

        Args:
            messages: List of message dicts with 'role' and 'content'.

        Returns:
            Dict with response text, usage, and metadata.
        """
        ...

    @abc.abstractmethod
    async def health_check(self) -> ProviderHealthStatus:
        """Check if the endpoint is available and configured."""
        ...
