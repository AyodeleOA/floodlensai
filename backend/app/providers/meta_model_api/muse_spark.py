from __future__ import annotations

import json
import logging
from typing import Any

from app.core.config import get_settings
from app.providers.base import ImageAnalysisProvider, ProviderHealthStatus
from app.providers.meta_model_api.client import MetaModelAPIClient
from app.schemas.ai_analysis import HazardDetection, MuseSparkAnalysisResult

logger = logging.getLogger(__name__)
settings = get_settings()

# Prompt version for tracking provenance
PROMPT_VERSION = "muse_spark_v1"

# Controlled prompt for image analysis
IMAGE_ANALYSIS_PROMPT = """You are a flood hazard analysis assistant. Analyze the provided image and identify any visible flood-related hazards.

Return a JSON object with this exact schema:
{
  "scene_summary": "Brief description of the overall scene",
  "hazards": [
    {
      "type": "floodwater | blocked_drain | overflowing_drain | damaged_road | exposed_infrastructure | other",
      "visible_evidence": "What you see that indicates this hazard",
      "confidence": 0.0 to 1.0,
      "severity_observation": "low | moderate | high | critical | unknown",
      "bounding_box": [x1, y1, x2, y2],
      "requires_human_verification": true
    }
  ],
  "water_presence": "none | possible | visible | extensive | uncertain",
  "infrastructure_observations": ["list of observations about infrastructure"],
  "limitations": ["list of analysis limitations"],
  "recommended_review_actions": ["list of recommended actions for human reviewers"]
}

Important rules:
- Distinguish between what you observe and what you infer.
- Confidence is model confidence, not a calibrated probability of flooding.
- Do not estimate exact water depth, flow velocity, or structural integrity.
- Do not predict future flooding probability.
- Mark all hazards as requiring human verification."""


class MuseSparkProvider(ImageAnalysisProvider):
    """Muse Spark image analysis adapter — Meta Model API.

    Primary multimodal scene interpretation and structured incident assessment.
    Returns schema-constrained JSON. Explicitly distinguishes observation from inference.
    """

    def __init__(self, client: MetaModelAPIClient | None = None) -> None:
        self.client = client or MetaModelAPIClient()
        self.model_id = settings.MUSE_SPARK_MODEL

    async def analyze_image(
        self,
        image_data: bytes | str,
        context: dict[str, Any] | None = None,
    ) -> MuseSparkAnalysisResult:
        """Analyze an image with Muse Spark and return normalised structured output.

        Validates model output against the strict internal schema.
        Rejects or safely repairs malformed JSON.
        """
        # Build the API request
        context_str = ""
        if context:
            context_str = f"\n\nContext: {json.dumps(context)}"

        payload: dict[str, Any] = {
            "model": self.model_id,
            "messages": [
                {"role": "system", "content": IMAGE_ANALYSIS_PROMPT},
                {"role": "user", "content": f"Analyze this image for flood-related hazards.{context_str}"},
            ],
            "response_format": {"type": "json_object"},
        }

        # Add image — this depends on the Meta API's multimodal format
        # Using base64 encoding or URL reference depending on the API spec
        if isinstance(image_data, bytes):
            import base64
            b64 = base64.b64encode(image_data).decode("utf-8")
            payload["messages"][1]["content"] = [
                {"type": "text", "text": f"Analyze this image for flood-related hazards.{context_str}"},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
            ]
        else:
            payload["messages"][1]["content"] = [
                {"type": "text", "text": f"Analyze this image for flood-related hazards.{context_str}"},
                {"type": "image_url", "image_url": {"url": image_data}},
            ]

        response = await self.client.post("chat/completions", payload)

        # Extract and validate the response
        return self._parse_response(response)

    def _parse_response(self, response: dict[str, Any]) -> MuseSparkAnalysisResult:
        """Parse and validate the Meta API response into the internal schema.

        Rejects or safely repairs malformed JSON. Never silently accepts
        unvalidated free text as structured risk data.
        """
        try:
            content = response.get("choices", [{}])[0].get("message", {}).get("content", "{}")
            if isinstance(content, str):
                parsed = json.loads(content)
            else:
                parsed = content
        except (json.JSONDecodeError, IndexError, KeyError) as e:
            logger.error(f"Failed to parse Muse Spark response: {e}")
            return MuseSparkAnalysisResult(
                scene_summary="Analysis failed — could not parse model output.",
                hazards=[],
                water_presence="uncertain",
                limitations=["Model response was not valid JSON and could not be parsed."],
                recommended_review_actions=["Request manual review of the image."],
            )

        # Validate and normalise against the strict schema
        try:
            hazards = []
            for h in parsed.get("hazards", []):
                hazards.append(HazardDetection(
                    type=h.get("type", "other"),
                    visible_evidence=h.get("visible_evidence", ""),
                    confidence=max(0.0, min(1.0, float(h.get("confidence", 0.0)))),
                    severity_observation=h.get("severity_observation", "unknown"),
                    bounding_box=h.get("bounding_box"),
                    requires_human_verification=h.get("requires_human_verification", True),
                ))

            return MuseSparkAnalysisResult(
                scene_summary=parsed.get("scene_summary", ""),
                hazards=hazards,
                water_presence=parsed.get("water_presence", "uncertain"),
                infrastructure_observations=parsed.get("infrastructure_observations", []),
                limitations=parsed.get("limitations", []),
                recommended_review_actions=parsed.get("recommended_review_actions", []),
            )
        except Exception as e:
            logger.error(f"Failed to validate Muse Spark response schema: {e}")
            return MuseSparkAnalysisResult(
                scene_summary="Analysis failed — model output did not match expected schema.",
                hazards=[],
                water_presence="uncertain",
                limitations=[f"Schema validation error: {e}"],
                recommended_review_actions=["Request manual review of the image."],
            )

    async def health_check(self) -> ProviderHealthStatus:
        """Check if Muse Spark is available and configured."""
        return await self.client.health_check()
