from __future__ import annotations

import uuid

import pytest


@pytest.mark.asyncio
async def test_create_report(client):
    """Test creating a new report."""
    response = await client.post("/api/v1/reports", json={
        "report_type": "flooding",
        "description": "Street flooding after heavy rain",
        "latitude": 6.4541,
        "longitude": 3.3947,
        "hazard_type": "floodwater",
        "severity": "high",
        "privacy_consent": True,
    })
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["status"] == "submitted"
    assert "receipt_url" in data


@pytest.mark.asyncio
async def test_create_report_invalid_coords(client):
    """Test that invalid coordinates are rejected."""
    response = await client.post("/api/v1/reports", json={
        "report_type": "flooding",
        "latitude": 999.0,  # invalid
        "longitude": 3.3947,
    })
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_report_invalid_severity(client):
    """Test that invalid severity is rejected."""
    response = await client.post("/api/v1/reports", json={
        "report_type": "flooding",
        "latitude": 6.4541,
        "longitude": 3.3947,
        "severity": "extreme",  # invalid
    })
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_report_receipt(client):
    """Test retrieving a report receipt."""
    # Create a report first
    create_response = await client.post("/api/v1/reports", json={
        "report_type": "flooding",
        "latitude": 6.4541,
        "longitude": 3.3947,
        "privacy_consent": True,
    })
    report_id = create_response.json()["id"]

    # Get receipt
    response = await client.get(f"/api/v1/reports/{report_id}/receipt")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == report_id
    assert "latitude_coarse" in data
    assert "longitude_coarse" in data
    # Coarse coords should be rounded
    assert len(str(data["latitude_coarse"]).split(".")[-1]) <= 2
    # Should not include private data
    assert "reporter_contact" not in data
    assert "description" not in data


@pytest.mark.asyncio
async def test_get_report_receipt_not_found(client):
    """Test 404 for non-existent report receipt."""
    fake_id = uuid.uuid4()
    response = await client.get(f"/api/v1/reports/{fake_id}/receipt")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_public_reports(client):
    """Test listing public reports."""
    # Create a few reports
    for i in range(3):
        await client.post("/api/v1/reports", json={
            "report_type": "flooding",
            "latitude": 6.45 + i * 0.01,
            "longitude": 3.39 + i * 0.01,
            "privacy_consent": True,
        })

    response = await client.get("/api/v1/reports/public")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) >= 3
    # Public reports should have coarse coordinates only
    for item in data["items"]:
        assert "latitude_coarse" in item
        assert "longitude_coarse" in item
        assert "reporter_contact" not in item
        assert "description" not in item
