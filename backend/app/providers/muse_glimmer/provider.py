from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

import httpx

from app.core.config import get_settings
from app.providers.base import (
    ImageAnalysisProvider,
    OpenWeightInferenceProvider,
    ProviderHealthStatus,
)
from app.schemas.ai_analysis import HazardDetection, MuseSparkAnalysisResult

logger = logging.getLogger(__name__)
settings = get_settings()


class MuseGlimmerProvider(OpenWeightInferenceProvider, ImageAnalysisProvider):
    """Muse Glimmer open-weight adapter — OpenAI-compatible endpoint.

    30B multimodal model (Apache 2.0). Calls an OpenAI-compatible private endpoint.
    Does not load model weights into the application.
    Configurable base URL, model name, timeout, and health check.

    Used for local/edge or separately hosted inference for offline-capable
    field hubs, private deployments, or fallback image interpretation.
    """

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        api_key: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        self.base_url = base_url or settings.MUSE_GLIMMER_BASE_URL
        self.model = model or settings.MUSE_GLIMMER_MODEL or "muse-glimmer"
        self.api_key = api_key or settings.MUSE_GLIMMER_API_KEY or "not-required"
        self.timeout = timeout
        self._enabled = settings.MUSE_GLIMMER_ENABLED and bool(self.base_url)

    async def chat_completion(
        self,
        messages: list[dict[str, str]],
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Send a chat completion request to the OpenAI-compatible endpoint."""
        if not self._enabled:
            raise RuntimeError("Muse Glimmer is not configured")

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.3),
            "max_tokens": kwargs.get("max_tokens", 2000),
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/v1/chat/completions",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
            return response.json()

    async def analyze_image(
        self,
        image_data: bytes | str,
        context: dict[str, Any] | None = None,
    ) -> MuseSparkAnalysisResult:
        """Analyze an image using Glimmer's multimodal capabilities.

        Uses the same internal schema as Muse Spark for consistency.
        """
        import base64
        import json

        if isinstance(image_data, bytes):
            b64 = base64.b64encode(image_data).decode("utf-8")
            image_content = f"data:image/jpeg;base64,{b64}"
        else:
            image_content = image_data

        messages = [
            {
                "role": "system",
                "content": (
                    "Analyze this image for flood-related hazards. "
                    "Return JSON with: scene_summary, hazards (type, visible_evidence, "
                    "confidence 0-1, severity_observation, requires_human_verification), "
                    "water_presence, infrastructure_observations, limitations, "
                    "recommended_review_actions."
                ),
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": f"Analyze for flood hazards. Context: {json.dumps(context or {})}"},
                    {"type": "image_url", "image_url": {"url": image_content}},
                ],
            },
        ]

        response = await self.chat_completion(messages)
        content = response.get("choices", [{}])[0].get("message", {}).get("content", "{}")

        try:
            parsed = json.loads(content) if isinstance(content, str) else content
        except json.JSONDecodeError:
            return MuseSparkAnalysisResult(
                scene_summary="Analysis failed — could not parse output.",
                limitations=["Glimmer response was not valid JSON."],
            )

        hazards = [
            HazardDetection(
                type=h.get("type", "other"),
                visible_evidence=h.get("visible_evidence", ""),
                confidence=max(0.0, min(1.0, float(h.get("confidence", 0.0)))),
                severity_observation=h.get("severity_observation", "unknown"),
                requires_human_verification=h.get("requires_human_verification", True),
            )
            for h in parsed.get("hazards", [])
        ]

        return MuseSparkAnalysisResult(
            scene_summary=parsed.get("scene_summary", ""),
            hazards=hazards,
            water_presence=parsed.get("water_presence", "uncertain"),
            infrastructure_observations=parsed.get("infrastructure_observations", []),
            limitations=parsed.get("limitations", []),
            recommended_review_actions=parsed.get("recommended_review_actions", []),
        )

    async def health_check(self) -> ProviderHealthStatus:
        """Check if the Glimmer endpoint is available and configured."""
        if not settings.MUSE_GLIMMER_ENABLED:
            return ProviderHealthStatus(
                status="not_configured",
                message="MUSE_GLIMMER_ENABLED is false",
                last_check=datetime.now(timezone.utc),
            )
        if not self.base_url:
            return ProviderHealthStatus(
                status="not_configured",
                message="MUSE_GLIMMER_BASE_URL not set",
                last_check=datetime.now(timezone.utc),
            )

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    f"{self.base_url}/v1/models",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                )
                if response.status_code == 200:
                    return ProviderHealthStatus(
                        status="connected",
                        message="Glimmer endpoint reachable",
                        last_check=datetime.now(timezone.utc),
                        endpoint=self.base_url,
                    )
                return ProviderHealthStatus(
                    status="unavailable",
                    message=f"Endpoint returned {response.status_code}",
                    last_check=datetime.now(timezone.utc),
                )
        except Exception as e:
            return ProviderHealthStatus(
                status="unavailable",
                message=str(e)[:200],
                last_check=datetime.now(timezone.utc),
            )
