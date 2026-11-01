from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx

from app.core.config import get_settings
from app.providers.base import ProviderHealthStatus

logger = logging.getLogger(__name__)
settings = get_settings()


class MetaModelAPIClient:
    """HTTP client for the Meta Model API.

    All Meta API credentials remain server-side. The browser never calls
    Meta Model API directly or receives MODEL_API_KEY.

    Includes:
    - Bearer token authentication
    - Retries with exponential backoff for transient errors
    - Respect for provider rate limits (429)
    - Timeout handling
    """

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        timeout: float = 30.0,
        max_retries: int = 3,
    ) -> None:
        self.base_url = base_url or settings.MODEL_API_BASE_URL
        self.api_key = api_key or settings.MODEL_API_KEY
        self.timeout = timeout
        self.max_retries = max_retries

    def _headers(self) -> dict[str, str]:
        """Build auth headers. Never expose the key in logs or responses."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def post(
        self,
        endpoint: str,
        payload: dict[str, Any],
        extra_headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Send a POST request with retries and exponential backoff.

        Raises httpx.HTTPStatusError for non-retryable errors (4xx except 429).
        Retries on 429, 5xx, and connection errors.
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = self._headers()
        if extra_headers:
            headers.update(extra_headers)

        last_error: Exception | None = None

        for attempt in range(self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(url, json=payload, headers=headers)

                    if response.status_code == 429:
                        # Rate limited — back off and retry
                        retry_after = response.headers.get("Retry-After", "2")
                        wait = float(retry_after) if retry_after.isdigit() else 2.0
                        logger.warning(f"Meta API rate limited (429), retrying after {wait}s")
                        if attempt < self.max_retries:
                            await asyncio.sleep(wait * (2 ** attempt))
                            continue
                        response.raise_for_status()

                    if 500 <= response.status_code < 600:
                        # Server error — retry with exponential backoff
                        if attempt < self.max_retries:
                            wait = 2.0 ** attempt
                            logger.warning(f"Meta API {response.status_code}, retrying after {wait}s")
                            await asyncio.sleep(wait)
                            continue
                        response.raise_for_status()

                    response.raise_for_status()
                    return response.json()

            except (httpx.ConnectError, httpx.TimeoutException) as e:
                last_error = e
                if attempt < self.max_retries:
                    wait = 2.0 ** attempt
                    logger.warning(f"Meta API connection error, retrying after {wait}s: {e}")
                    await asyncio.sleep(wait)
                    continue
                raise

        raise last_error or RuntimeError("Max retries exceeded")

    async def get(self, endpoint: str) -> dict[str, Any]:
        """Send a GET request."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url, headers=self._headers())
            response.raise_for_status()
            return response.json()

    async def health_check(self) -> ProviderHealthStatus:
        """Check if the Meta Model API is reachable and credentials are configured."""
        from datetime import datetime, timezone

        if not self.api_key:
            return ProviderHealthStatus(
                status="not_configured",
                message="MODEL_API_KEY not set",
                last_check=datetime.now(timezone.utc),
            )

        try:
            # Try a lightweight endpoint to check connectivity
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    f"{self.base_url}/models",
                    headers=self._headers(),
                )
                if response.status_code == 200:
                    return ProviderHealthStatus(
                        status="connected",
                        message="Meta Model API reachable",
                        last_check=datetime.now(timezone.utc),
                        endpoint=self.base_url,
                    )
                return ProviderHealthStatus(
                    status="unavailable",
                    message=f"Meta API returned {response.status_code}",
                    last_check=datetime.now(timezone.utc),
                )
        except Exception as e:
            return ProviderHealthStatus(
                status="unavailable",
                message=str(e)[:200],
                last_check=datetime.now(timezone.utc),
            )
