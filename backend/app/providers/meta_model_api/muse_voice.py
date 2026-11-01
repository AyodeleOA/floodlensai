from __future__ import annotations

import logging
from typing import Any

from app.core.config import get_settings
from app.providers.base import ProviderHealthStatus, VoiceTranscriptionProvider
from app.providers.meta_model_api.client import MetaModelAPIClient

logger = logging.getLogger(__name__)
settings = get_settings()


class MuseVoiceProvider(VoiceTranscriptionProvider):
    """Muse Voice Transcribe adapter — Meta Model API.

    Converts resident voice reports to text.
    Preserves original audio privately. Stores transcript, language if available,
    timestamps, and transcription status. User can edit transcript.
    """

    def __init__(self, client: MetaModelAPIClient | None = None) -> None:
        self.client = client or MetaModelAPIClient()
        self.model_id = settings.MUSE_VOICE_MODEL

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
        if isinstance(audio_data, bytes):
            import base64
            b64 = base64.b64encode(audio_data).decode("utf-8")
            audio_input = f"data:audio/webm;base64,{b64}"
        else:
            audio_input = audio_data

        payload: dict[str, Any] = {
            "model": self.model_id,
            "audio": audio_input,
        }
        if language:
            payload["language"] = language

        response = await self.client.post("audio/transcriptions", payload)

        return {
            "transcript": response.get("text", ""),
            "language": response.get("language", language),
            "confidence": response.get("confidence", 0.0),
            "duration_ms": response.get("duration_ms", 0),
            "timestamps": response.get("timestamps", []),
            "status": "completed",
        }

    async def health_check(self) -> ProviderHealthStatus:
        """Check if Muse Voice Transcribe is available and configured."""
        return await self.client.health_check()
