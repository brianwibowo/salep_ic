"""API endpoint integration tests for SALEP RBAC."""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_serve_dashboard():
    """Dashboard HTML should be served with 200 OK."""
    response = client.get("/")
    assert response.status_code == 200
    assert "SALEP" in response.text
    assert "login-screen" in response.text
    assert "workspace-marketing" in response.text
    assert "workspace-sales" in response.text


def test_get_leads_marketing():
    """Marketing should get all leads."""
    response = client.get("/api/v1/leads?role=marketing")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2


def test_get_leads_sales():
    """Sales should ONLY get valid leads."""
    response = client.get("/api/v1/leads?role=sales")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    for lead in data:
        assert lead["marketing_status"] == "valid"


def test_get_lead_stats():
    """Stats endpoint returns total, valid, pending, invalid."""
    response = client.get("/api/v1/leads/stats")
    assert response.status_code == 200
    stats = response.json()
    assert "total" in stats
    assert "valid" in stats
    assert "pending" in stats
    assert "invalid" in stats


def test_update_status_and_sales_visibility():
    """Updating status from marketing updates visibility in sales."""
    # Fetch marketing leads
    response = client.get("/api/v1/leads?role=marketing&status=all")
    leads = response.json()
    lead_id = leads[0]["lead_id"]

    # Mark as invalid
    resp_patch = client.patch(f"/api/v1/leads/{lead_id}/status", json={"marketing_status": "invalid"})
    assert resp_patch.status_code == 200
    assert resp_patch.json()["marketing_status"] == "invalid"

    # Confirm not in sales
    sales_resp = client.get("/api/v1/leads?role=sales")
    assert not any(l["lead_id"] == lead_id for l in sales_resp.json())

    # Mark as valid
    resp_patch2 = client.patch(f"/api/v1/leads/{lead_id}/status", json={"marketing_status": "valid"})
    assert resp_patch2.status_code == 200
    assert resp_patch2.json()["marketing_status"] == "valid"

    # Confirm now in sales!
    sales_resp2 = client.get("/api/v1/leads?role=sales")
    assert any(l["lead_id"] == lead_id for l in sales_resp2.json())
