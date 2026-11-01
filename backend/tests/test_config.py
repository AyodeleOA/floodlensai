from __future__ import annotations

from app.core.config import AIProviderMode, AppEnv, get_settings


def test_settings_defaults():
    """Test that default settings load correctly."""
    settings = get_settings()
    assert settings.APP_NAME == "FloodLens AI"
    assert settings.API_V1_PREFIX == "/api/v1"
    assert settings.RISK_GRID_SYSTEM == "h3"
    assert settings.RISK_GRID_RESOLUTION == 8


def test_settings_demo_mode():
    """Test demo mode detection."""
    settings = get_settings()
    assert settings.is_demo() is True


def test_settings_ai_mode():
    """Test AI provider mode in test env."""
    settings = get_settings()
    assert settings.AI_PROVIDER_MODE == AIProviderMode.mock
    assert settings.is_ai_enabled() is False


def test_config_summary_no_secrets():
    """Test that config summary never includes secrets."""
    settings = get_settings()
    summary = settings.config_summary()
    assert "MODEL_API_KEY" not in summary
    assert "DATABASE_URL" not in summary
    assert "api_key" not in str(summary).lower()
    assert "demo_mode" in summary
