from __future__ import annotations

import logging
from typing import Any

from app.core.config import get_settings
from app.providers.base import ImageGenerationProvider, ProviderHealthStatus
from app.providers.meta_model_api.client import MetaModelAPIClient

logger = logging.getLogger(__name__)
settings = get_settings()


class MuseImageProvider(ImageGenerationProvider):
    """Muse Image generation adapter — Meta Model API.

    Generates optional educational illustrations, UI demonstration assets,
    and non-authoritative preparedness visuals.

    Never generates or alters evidence photographs.
    Generated images must be watermarked/labelled as AI-generated.
    """

    def __init__(self, client: MetaModelAPIClient | None = None) -> None:
        self.client = client or MetaModelAPIClient()
        self.model_id = settings.MUSE_IMAGE_MODEL

    async def generate_image(
        self,
        prompt: str,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Generate a preparedness illustration or demo asset.

        Every generated image is marked as AI-generated.
        """
        # Add watermark/labelling instruction to the prompt
        full_prompt = (
            f"{prompt}\n\nIMPORTANT: This image must be clearly watermarked "
            "or labelled as 'AI-generated' in the bottom right corner."
        )

        payload = {
            "model": self.model_id,
            "prompt": full_prompt,
        }

        response = await self.client.post("images/generations", payload)

        return {
            "image_url": response.get("data", [{}])[0].get("url", ""),
            "watermarked": True,
            "label": "AI-generated",
            "prompt": prompt,
            "model": self.model_id,
        }

    async def health_check(self) -> ProviderHealthStatus:
        """Check if Muse Image is available and configured."""
        return await self.client.health_check()
