from __future__ import annotations

import logging
from typing import Any

from app.core.config import get_settings
from app.providers.base import EvidenceSynthesisProvider, ProviderHealthStatus
from app.providers.meta_model_api.client import MetaModelAPIClient

logger = logging.getLogger(__name__)
settings = get_settings()


class MuseWonderProvider(EvidenceSynthesisProvider):
    """Muse Wonder evidence synthesis adapter — Meta Model API.

    Used for reviewer-requested complex synthesis across multiple reports
    and environmental observations. Not called for every image.
    Produces evidence-linked explanation and uncertainty.
    """

    def __init__(self, client: MetaModelAPIClient | None = None) -> None:
        self.client = client or MetaModelAPIClient()
        self.model_id = settings.MUSE_WONDER_MODEL

    async def synthesize_evidence(
        self,
        evidence_items: list[dict[str, Any]],
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Synthesize multiple evidence items into a coherent assessment."""
        import json

        prompt = (
            "You are a flood analysis assistant. Synthesize the following evidence "
            "items into a coherent assessment. Link your summary to source report IDs. "
            "Identify missing or conflicting evidence. Do not make claims beyond what "
            "the evidence supports.\n\n"
        )
        prompt += f"Context: {json.dumps(context or {})}\n\n"
        prompt += f"Evidence items: {json.dumps(evidence_items, indent=2)}\n\n"
        prompt += (
            "Return a JSON object with: summary, key_findings[], uncertainty_level, "
            "source_report_ids[], missing_evidence[], conflicting_evidence[]"
        )

        payload = {
            "model": self.model_id,
            "messages": [
                {"role": "system", "content": "You are a flood evidence synthesis assistant."},
                {"role": "user", "content": prompt},
            ],
            "response_format": {"type": "json_object"},
        }

        response = await self.client.post("chat/completions", payload)

        try:
            content = response.get("choices", [{}])[0].get("message", {}).get("content", "{}")
            if isinstance(content, str):
                return __import__("json").loads(content)
            return content
        except Exception as e:
            logger.error(f"Failed to parse Muse Wonder response: {e}")
            return {
                "summary": "Synthesis failed — could not parse model output.",
                "key_findings": [],
                "uncertainty_level": "high",
                "source_report_ids": [],
                "missing_evidence": ["Model response parsing failed"],
                "conflicting_evidence": [],
            }

    async def health_check(self) -> ProviderHealthStatus:
        """Check if Muse Wonder is available and configured."""
        return await self.client.health_check()
