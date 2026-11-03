from __future__ import annotations

from enum import Enum
from functools import lru_cache
from typing import Any

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppEnv(str, Enum):
    local = "local"
    dev = "dev"
    demo = "demo"
    prod = "prod"


class AIProviderMode(str, Enum):
    mock = "mock"
    demo = "demo"
    live = "live"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- Core app ---
    APP_ENV: AppEnv = AppEnv.local
    APP_NAME: str = "FloodLens AI"
    API_V1_PREFIX: str = "/api/v1"
    FRONTEND_ORIGIN: str = "https://main.dmpm2yei4pgxa.amplifyapp.com/"

    # --- Database ---
    DATABASE_URL: str = "postgresql+psycopg://floodlens:FloodlenPass123@floodlens-ai-floodlensdb-xia8dz2hw3om.cstm08qqy3w3.us-east-1.rds.amazonaws.com:5432/floodlens"

    # --- S3 / AWS ---
    S3_MEDIA_BUCKET: str = ""
    AWS_REGION: str = "us-east-1"
    AWS_ENDPOINT_URL: str = ""

    # --- Meta Model API ---
    MODEL_API_BASE_URL: str = "https://api.meta.ai/v1"
    MODEL_API_KEY: str = ""
    MUSE_SPARK_MODEL: str = "muse-spark-1.3"
    MUSE_WONDER_MODEL: str = "muse-wonder-1.0"
    MUSE_IMAGE_MODEL: str = "muse-image-1.0"
    MUSE_VOICE_MODEL: str = "muse-voice-transcribe-1.0"
    SAM_MODEL: str = "sam-3.1"

    # --- Open-weight adapters ---
    MUSE_GLIMMER_ENABLED: bool = False
    MUSE_GLIMMER_BASE_URL: str = ""
    MUSE_GLIMMER_MODEL: str = ""
    MUSE_GLIMMER_API_KEY: str = ""

    MUSE_SPARK_OPEN_ENABLED: bool = False
    MUSE_SPARK_OPEN_BASE_URL: str = ""
    MUSE_SPARK_OPEN_MODEL: str = ""
    MUSE_SPARK_OPEN_API_KEY: str = ""

    # --- AI feature flags ---
    AI_PROVIDER_MODE: AIProviderMode = AIProviderMode.mock
    ENABLE_AI_IMAGE_ANALYSIS: bool = False
    ENABLE_AI_VOICE_TRANSCRIPTION: bool = False
    ENABLE_SAM_SEGMENTATION: bool = False
    ENABLE_MUSE_IMAGE_GENERATION: bool = False
    ENABLE_MUSE_WONDER_ANALYST: bool = False

    # --- SQS ---
    SQS_MEDIA_ANALYSIS_QUEUE_URL: str = ""
    SQS_MEDIA_ANALYSIS_DLQ_URL: str = ""

    # --- Cognito ---
    COGNITO_USER_POOL_ID: str = ""
    COGNITO_CLIENT_ID: str = ""

    # --- Risk engine ---
    RISK_WEIGHTS_PROFILE: str = "illustrative_unvalidated"
    RISK_GRID_SYSTEM: str = "h3"
    RISK_GRID_RESOLUTION: int = 8

    # --- Demo ---
    DEMO_MODE: bool = True

    @field_validator("RISK_GRID_RESOLUTION")
    @classmethod
    def validate_grid_resolution(cls, v: int) -> int:
        if not 0 <= v <= 15:
            raise ValueError("RISK_GRID_RESOLUTION must be between 0 and 15")
        return v

    def is_ai_enabled(self) -> bool:
        return self.AI_PROVIDER_MODE != AIProviderMode.mock

    def is_demo(self) -> bool:
        return self.DEMO_MODE or self.APP_ENV == AppEnv.demo

    def config_summary(self) -> dict[str, Any]:
        """Return a safe summary of config for logging at startup. Never includes secrets."""
        return {
            "app_env": self.APP_ENV.value,
            "app_name": self.APP_NAME,
            "api_prefix": self.API_V1_PREFIX,
            "frontend_origin": self.FRONTEND_ORIGIN,
            "ai_provider_mode": self.AI_PROVIDER_MODE.value,
            "enable_ai_image_analysis": self.ENABLE_AI_IMAGE_ANALYSIS,
            "enable_ai_voice_transcription": self.ENABLE_AI_VOICE_TRANSCRIPTION,
            "enable_sam_segmentation": self.ENABLE_SAM_SEGMENTATION,
            "enable_muse_image_generation": self.ENABLE_MUSE_IMAGE_GENERATION,
            "enable_muse_wonder_analyst": self.ENABLE_MUSE_WONDER_ANALYST,
            "muse_glimmer_enabled": self.MUSE_GLIMMER_ENABLED,
            "muse_spark_open_enabled": self.MUSE_SPARK_OPEN_ENABLED,
            "risk_weights_profile": self.RISK_WEIGHTS_PROFILE,
            "risk_grid_system": self.RISK_GRID_SYSTEM,
            "risk_grid_resolution": self.RISK_GRID_RESOLUTION,
            "demo_mode": self.DEMO_MODE,
            "s3_configured": bool(self.S3_MEDIA_BUCKET),
            "model_api_configured": bool(self.MODEL_API_KEY),
            "sqs_configured": bool(self.SQS_MEDIA_ANALYSIS_QUEUE_URL),
        }


@lru_cache
def get_settings() -> Settings:
    return Settings()
