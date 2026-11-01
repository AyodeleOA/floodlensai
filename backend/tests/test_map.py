from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_map_summary(client):
    """Test map summary endpoint."""
    response = await client.get("/api/v1/map/summary")
    assert response.status_code == 200
    data = response.json()
    assert "total_reports" in data
    assert "verified_incidents" in data
    assert "pending_reports" in data
    assert "high_risk_cells" in data
    assert "last_updated" in data


@pytest.mark.asyncio
async def test_map_reports(client):
    """Test map reports endpoint."""
    response = await client.get("/api/v1/map/reports")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_map_risk_cells(client):
    """Test map risk cells endpoint."""
    response = await client.get("/api/v1/map/risk-cells")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data


@pytest.mark.asyncio
async def test_map_layers(client):
    """Test layers endpoint."""
    response = await client.get("/api/v1/map/layers")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # Should have at least the default layers
    layer_ids = [l["id"] for l in data]
    assert "reports" in layer_ids
    assert "risk-cells" in layer_ids


@pytest.mark.asyncio
async def test_system_capabilities(client):
    """Test system capabilities endpoint."""
    response = await client.get("/api/v1/system/capabilities")
    assert response.status_code == 200
    data = response.json()
    assert data["app_name"] == "FloodLens AI"
    assert "demo_mode" in data
    assert "features" in data
    assert "enabled_layers" in data
    assert "disclaimer" in data
    assert "AI-generated" not in str(data)  # No secrets
    # Disclaimer text should be present
    assert "not an official emergency warning" in data["disclaimer"]["text"].lower()
