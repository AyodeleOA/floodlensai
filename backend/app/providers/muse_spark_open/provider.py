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


class MuseSparkOpenProvider(OpenWeightInferenceProvider, ImageAnalysisProvider):
    """Muse Spark Open adapter — private GPU endpoint.

    816B total / 42B active sparse MoE. Requires specialised multi-GPU infrastructure.
    This is an advanced optional inference profile for a separately funded GPU deployment
    or partner-hosted endpoint. NOT a default MVP dependency.

    Keep this adapter disabled unless credentials and endpoint are configured.
    If no endpoint is available, use Muse Spark hosted inference for the user-facing
    workflow and clearly show that this adapter is not connected.
    """

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        api_key: str | None = None,
        timeout: float = 60.0,
    ) -> None:
        self.base_url = base_url or settings.MUSE_SPARK_OPEN_BASE_URL
        self.model = model or settings.MUSE_SPARK_OPEN_MODEL or "muse-spark-open"
        self.api_key = api_key or settings.MUSE_SPARK_OPEN_API_KEY or "not-required"
        self.timeout = timeout
        self._enabled = settings.MUSE_SPARK_OPEN_ENABLED and bool(self.base_url)

    async def chat_completion(
        self,
        messages: list[dict[str, str]],
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Send a chat completion request to the partner-hosted endpoint."""
        if not self._enabled:
            raise RuntimeError("Muse Spark Open is not configured")

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
        """Analyze an image using Spark Open's multimodal capabilities."""
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
                    "Return JSON with: scene_summary, hazards, water_presence, "
                    "infrastructure_observations, limitations, recommended_review_actions."
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
                limitations=["Spark Open response was not valid JSON."],
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
        """Check if the Spark Open endpoint is available and configured."""
        if not settings.MUSE_SPARK_OPEN_ENABLED:
            return ProviderHealthStatus(
                status="not_configured",
                message="MUSE_SPARK_OPEN_ENABLED is false",
                last_check=datetime.now(timezone.utc),
            )
        if not self.base_url:
            return ProviderHealthStatus(
                status="not_configured",
                message="MUSE_SPARK_OPEN_BASE_URL not set",
                last_check=datetime.now(timezone.utc),
            )

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.base_url}/v1/models",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                )
                if response.status_code == 200:
                    return ProviderHealthStatus(
                        status="connected",
                        message="Spark Open endpoint reachable",
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
