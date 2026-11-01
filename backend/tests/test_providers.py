from __future__ import annotations

import pytest

from app.providers.demo.provider import (
    DemoEvidenceSynthesisProvider,
    DemoImageAnalysisProvider,
    DemoImageGenerationProvider,
    DemoSegmentationProvider,
    DemoVoiceProvider,
)


@pytest.mark.asyncio
async def test_demo_image_analysis():
    """Test demo image analysis returns valid structured output."""
    provider = DemoImageAnalysisProvider()
    result = await provider.analyze_image(b"fake_image_data", {"report_id": "test"})
    assert result.scene_summary is not None
    assert "Demo analysis" in result.scene_summary
    assert len(result.hazards) > 0
    assert result.hazards[0].type == "floodwater"
    assert 0 <= result.hazards[0].confidence <= 1.0
    assert result.water_presence == "visible"
    assert len(result.limitations) > 0
    assert "Demo analysis" in result.limitations[0]


@pytest.mark.asyncio
async def test_demo_segmentation():
    """Test demo segmentation returns masks and boxes."""
    provider = DemoSegmentationProvider()
    result = await provider.segment_image(b"fake_image", objects=["floodwater", "debris"])
    assert "masks" in result
    assert "bounding_boxes" in result
    assert "object_labels" in result
    assert result["status"] == "completed"


@pytest.mark.asyncio
async def test_demo_voice_transcription():
    """Test demo voice transcription returns transcript."""
    provider = DemoVoiceProvider()
    result = await provider.transcribe(b"fake_audio")
    assert result["transcript"] is not None
    assert len(result["transcript"]) > 0
    assert result["status"] == "completed"
    assert result["confidence"] > 0


@pytest.mark.asyncio
async def test_demo_evidence_synthesis():
    """Test demo evidence synthesis returns structured summary."""
    provider = DemoEvidenceSynthesisProvider()
    result = await provider.synthesize_evidence([
        {"report_id": "abc", "description": "flooding report"},
    ])
    assert "summary" in result
    assert "Demo synthesis" in result["summary"]
    assert "key_findings" in result
    assert "uncertainty_level" in result


@pytest.mark.asyncio
async def test_demo_image_generation():
    """Test demo image generation returns watermarked label."""
    provider = DemoImageGenerationProvider()
    result = await provider.generate_image("flood preparedness illustration")
    assert result["watermarked"] is True
    assert "AI-generated" in result["label"]
    assert result["status"] == "completed"


@pytest.mark.asyncio
async def test_demo_health_checks():
    """Test all demo providers return demo_mode health status."""
    providers = [
        DemoImageAnalysisProvider(),
        DemoSegmentationProvider(),
        DemoVoiceProvider(),
        DemoEvidenceSynthesisProvider(),
        DemoImageGenerationProvider(),
    ]
    for provider in providers:
        health = await provider.health_check()
        assert health.status == "demo_mode"


@pytest.mark.asyncio
async def test_model_router_demo_mode():
    """Test that the ModelRouter uses demo providers in mock mode."""
    from app.services.model_router.router import ModelRouter

    router = ModelRouter()
    assert router.is_demo is True
    assert router.provider_name == "demo"

    result, provider_name = await router.analyze_image(b"fake")
    assert provider_name == "demo"
    assert result.scene_summary is not None
