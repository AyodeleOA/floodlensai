from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_health_live(client):
    """Test the liveness probe."""
    response = await client.get("/health/live")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_health_ready(client):
    """Test the readiness probe."""
    response = await client.get("/health/ready")
    assert response.status_code == 200
    data = response.json()
    # With SQLite in-memory, DB should be connected
    assert data["status"] in ("ok", "degraded")


@pytest.mark.asyncio
async def test_openapi_docs(client):
    """Test that OpenAPI docs endpoint is accessible."""
    response = await client.get("/docs")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_openapi_schema(client):
    """Test that the OpenAPI schema is available."""
    response = await client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert schema["info"]["title"] == "FloodLens AI"
