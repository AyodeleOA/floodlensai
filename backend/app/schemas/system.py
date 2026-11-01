from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.common import Disclaimer


class SystemCapabilities(BaseModel):
    """Safe frontend feature flags, provider status, and enabled layers. Never returns secrets."""

    app_name: str
    app_env: str
    demo_mode: bool
    ai_provider_mode: str
    features: dict[str, bool] = Field(default_factory=dict)
    enabled_layers: list[str] = Field(default_factory=list)
    model_statuses: list[dict[str, str]] = Field(default_factory=list)
    disclaimer: Disclaimer = Field(default_factory=Disclaimer)
    api_version: str = "v1"
    server_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
