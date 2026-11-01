from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_admin_reports_requires_auth(client):
    """Test that admin endpoints require reviewer role."""
    response = await client.get("/api/v1/admin/reports")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_admin_reports_list(client, mock_user_headers):
    """Test admin reports list with auth."""
    response = await client.get("/api/v1/admin/reports", headers=mock_user_headers)
    assert response.status_code == 200
    data = response.json()
    assert "items" in data


@pytest.mark.asyncio
async def test_admin_analytics(client, mock_user_headers):
    """Test analytics overview endpoint."""
    response = await client.get("/api/v1/admin/analytics/overview", headers=mock_user_headers)
    assert response.status_code == 200
    data = response.json()
    assert "total_reports" in data
    assert "verified_incidents" in data
    assert "pending_review" in data
    assert "high_risk_zones" in data
    assert "open_reports" in data


@pytest.mark.asyncio
async def test_admin_model_status(client, mock_user_headers):
    """Test model status endpoint."""
    response = await client.get("/api/v1/admin/model-status", headers=mock_user_headers)
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "ai_provider_mode" in data
    assert "demo_mode" in data
    # Should list all model adapters
    model_ids = [m["id"] for m in data["items"]]
    assert "muse_spark" in model_ids
    assert "muse_glimmer" in model_ids
    assert "muse_spark_open" in model_ids


@pytest.mark.asyncio
async def test_admin_data_source_status(client, mock_user_headers):
    """Test data source status endpoint."""
    response = await client.get("/api/v1/admin/data-source-status", headers=mock_user_headers)
    assert response.status_code == 200
    data = response.json()
    assert "items" in data


@pytest.mark.asyncio
async def test_admin_hotspots(client, mock_user_headers):
    """Test hotspots endpoint."""
    response = await client.get("/api/v1/admin/hotspots", headers=mock_user_headers)
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_report_verify(client, mock_user_headers):
    """Test verifying a report."""
    # Create a report first
    create_response = await client.post("/api/v1/reports", json={
        "report_type": "flooding",
        "latitude": 6.4541,
        "longitude": 3.3947,
        "privacy_consent": True,
    })
    report_id = create_response.json()["id"]

    # Verify it
    response = await client.post(
        f"/api/v1/admin/reports/{report_id}/verify",
        json={"reason": "Confirmed flooding via field inspection"},
        headers=mock_user_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "verified"


@pytest.mark.asyncio
async def test_report_status_update(client, mock_user_headers):
    """Test updating report status."""
    # Create a report
    create_response = await client.post("/api/v1/reports", json={
        "report_type": "flooding",
        "latitude": 6.4541,
        "longitude": 3.3947,
        "privacy_consent": True,
    })
    report_id = create_response.json()["id"]

    # Update status
    response = await client.patch(
        f"/api/v1/admin/reports/{report_id}/status",
        json={"status": "under_review", "reason": "Starting review"},
        headers=mock_user_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "under_review"
