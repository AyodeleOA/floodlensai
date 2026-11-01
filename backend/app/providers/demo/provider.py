from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.providers.base import (
    EvidenceSynthesisProvider,
    ImageAnalysisProvider,
    ImageGenerationProvider,
    ProviderHealthStatus,
    SegmentationProvider,
    VoiceTranscriptionProvider,
)
from app.schemas.ai_analysis import HazardDetection, MuseSparkAnalysisResult


class DemoImageAnalysisProvider(ImageAnalysisProvider):
    """Demo/mock image analysis provider.

    Returns realistic fixture responses clearly labelled as demo.
    Never silently used — the UI must show 'Demo analysis' if fixtures are used.
    """

    async def analyze_image(
        self,
        image_data: bytes | str,
        context: dict[str, Any] | None = None,
    ) -> MuseSparkAnalysisResult:
        return MuseSparkAnalysisResult(
            scene_summary=(
                "Demo analysis: The image shows a flooded street with standing water "
                "covering the road surface. Several buildings appear to be adjacent to "
                "the flooded area."
            ),
            hazards=[
                HazardDetection(
                    type="floodwater",
                    visible_evidence="Standing water covering road surface in the lower portion of the image.",
                    confidence=0.82,
                    severity_observation="high",
                    bounding_box=[50, 300, 800, 600],
                    requires_human_verification=True,
                ),
                HazardDetection(
                    type="blocked_drain",
                    visible_evidence="Debris visible near what appears to be a drain opening.",
                    confidence=0.55,
                    severity_observation="moderate",
                    bounding_box=[320, 420, 400, 480],
                    requires_human_verification=True,
                ),
            ],
            water_presence="visible",
            infrastructure_observations=[
                "Road surface partially submerged",
                "Adjacent buildings appear intact",
            ],
            limitations=[
                "Demo analysis — not from a live model",
                "Cannot assess water depth or flow velocity from a single image",
                "Bounding boxes are illustrative only",
            ],
            recommended_review_actions=[
                "Verify location and time with reporter",
                "Cross-reference with recent rainfall data",
                "Check for duplicate reports in the same area",
            ],
        )

    async def health_check(self) -> ProviderHealthStatus:
        return ProviderHealthStatus(
            status="demo_mode",
            message="Demo image analysis provider active",
            last_check=datetime.now(timezone.utc),
        )


class DemoSegmentationProvider(SegmentationProvider):
    """Demo/mock segmentation provider."""

    async def segment_image(
        self,
        image_data: bytes | str,
        prompt_text: str | None = None,
        objects: list[str] | None = None,
    ) -> dict[str, Any]:
        labels = objects or ["floodwater", "drain opening", "debris", "road surface"]
        return {
            "masks": [
                {"label": labels[0] if labels else "floodwater", "confidence": 0.85},
                {"label": labels[1] if len(labels) > 1 else "debris", "confidence": 0.62},
            ],
            "bounding_boxes": [
                [50, 300, 800, 600],
                [320, 420, 400, 480],
            ],
            "object_labels": labels,
            "model_id": "demo-sam",
            "status": "completed",
        }

    async def health_check(self) -> ProviderHealthStatus:
        return ProviderHealthStatus(
            status="demo_mode",
            message="Demo segmentation provider active",
            last_check=datetime.now(timezone.utc),
        )


class DemoVoiceProvider(VoiceTranscriptionProvider):
    """Demo/mock voice transcription provider."""

    async def transcribe(
        self,
        audio_data: bytes | str,
        language: str | None = None,
    ) -> dict[str, Any]:
        return {
            "transcript": (
                "There is heavy flooding on my street. The water is up to my knees. "
                "The drain near the market is blocked and the water is not going down. "
                "Please send help to check the area."
            ),
            "language": language or "en",
            "confidence": 0.78,
            "duration_ms": 12000,
            "timestamps": [],
            "status": "completed",
        }

    async def health_check(self) -> ProviderHealthStatus:
        return ProviderHealthStatus(
            status="demo_mode",
            message="Demo voice transcription provider active",
            last_check=datetime.now(timezone.utc),
        )


class DemoEvidenceSynthesisProvider(EvidenceSynthesisProvider):
    """Demo/mock evidence synthesis provider."""

    async def synthesize_evidence(
        self,
        evidence_items: list[dict[str, Any]],
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return {
            "summary": (
                "Demo synthesis: Multiple reports from this area indicate persistent flooding "
                "over the past 48 hours. The evidence suggests a drainage issue contributing "
                "to water accumulation."
            ),
            "key_findings": [
                "3 reports of flooding within 500m in the last 48 hours",
                "1 verified blocked drain report nearby",
                "Rainfall data shows significant accumulation",
            ],
            "uncertainty_level": "moderate",
            "source_report_ids": [str(e.get("report_id", "")) for e in evidence_items if e.get("report_id")],
            "missing_evidence": [
                "No elevation/slope data available for this cell",
                "Historical flood records not yet integrated",
            ],
            "conflicting_evidence": [],
        }

    async def health_check(self) -> ProviderHealthStatus:
        return ProviderHealthStatus(
            status="demo_mode",
            message="Demo evidence synthesis provider active",
            last_check=datetime.now(timezone.utc),
        )


class DemoImageGenerationProvider(ImageGenerationProvider):
    """Demo/mock image generation provider."""

    async def generate_image(
        self,
        prompt: str,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return {
            "image_url": "",
            "watermarked": True,
            "label": "AI-generated (demo)",
            "prompt": prompt,
            "model": "demo-muse-image",
            "status": "completed",
        }

    async def health_check(self) -> ProviderHealthStatus:
        return ProviderHealthStatus(
            status="demo_mode",
            message="Demo image generation provider active",
            last_check=datetime.now(timezone.utc),
        )
