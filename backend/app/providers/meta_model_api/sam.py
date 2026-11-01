from __future__ import annotations

import logging
from typing import Any

from app.core.config import get_settings
from app.providers.base import ProviderHealthStatus, SegmentationProvider
from app.providers.meta_model_api.client import MetaModelAPIClient

logger = logging.getLogger(__name__)
settings = get_settings()


class SAMSegmentationProvider(SegmentationProvider):
    """SAM 3.1 segmentation adapter — Meta Model API.

    Segments objects/regions in submitted photos or video frames.
    Prompts for visible objects such as floodwater, drain opening, debris,
    road surface, vehicle, or building. Stores masks/boxes and source-media linkage.
    """

    def __init__(self, client: MetaModelAPIClient | None = None) -> None:
        self.client = client or MetaModelAPIClient()
        self.model_id = settings.SAM_MODEL

    async def segment_image(
        self,
        image_data: bytes | str,
        prompt_text: str | None = None,
        objects: list[str] | None = None,
    ) -> dict[str, Any]:
        """Segment objects in an image using SAM 3.1.

        Args:
            image_data: Raw image bytes or S3 key/URL.
            prompt_text: Optional text prompt for targeted segmentation.
            objects: List of object names (floodwater, drain, debris, etc.).

        Returns:
            Dict with masks, bounding_boxes, and object_labels.
        """
        if isinstance(image_data, bytes):
            import base64
            b64 = base64.b64encode(image_data).decode("utf-8")
            image_input = f"data:image/jpeg;base64,{b64}"
        else:
            image_input = image_data

        default_objects = ["floodwater", "drain opening", "debris", "road surface", "vehicle", "building"]
        target_objects = objects or default_objects

        payload: dict[str, Any] = {
            "model": self.model_id,
            "image": image_input,
            "prompts": prompt_text or ", ".join(target_objects),
            "objects": target_objects,
        }

        response = await self.client.post("vision/segment", payload)

        # Normalise response
        return {
            "masks": response.get("masks", []),
            "bounding_boxes": response.get("bounding_boxes", []),
            "object_labels": response.get("object_labels", target_objects),
            "model_id": self.model_id,
            "status": "completed",
        }

    async def health_check(self) -> ProviderHealthStatus:
        """Check if SAM 3.1 is available and configured."""
        return await self.client.health_check()
