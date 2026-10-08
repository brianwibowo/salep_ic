from __future__ import annotations

import httpx
import pytest
from fastapi.testclient import TestClient

from app.sources import spse_source
from app.sources.spse_source import SPSESourceAdapter
from app.main import app
from app.core import auth
from app.api.routes import leads
from app.services.lead_repository import LeadRepository


@pytest.mark.asyncio
async def test_spse_adapter_extracts_only_keyword_matching_tender(monkeypatch):
    html = "<script>var config = {authenticityToken: 'public-token'};</script>"
    page_data = {"draw": "1", "recordsTotal": 2, "recordsFiltered": 2, "data": [
        ["123", "Pengadaan Software ERP", "Badan X", "Berlangsung", "Rp. 100.000.000,00", "Tender", "Barang", "Harga Terendah", "TA 2026"],
        ["456", "Pengadaan meja kantor", "Badan Y", "Berlangsung", "Rp. 10.000.000,00", "Tender", "Barang", "Harga Terendah", "TA 2026"],
    ]}
    original = httpx.AsyncClient
    def handler(request):
        if request.method == "GET":
            return httpx.Response(200, text=html)
        return httpx.Response(200, json=page_data)
    monkeypatch.setattr(
        spse_source.httpx,
        "AsyncClient",
        lambda **kwargs: original(transport=httpx.MockTransport(handler)),
    )

    results = await SPSESourceAdapter().search(["software", "ERP"], limit=10)

    assert len(results) == 1
    assert results[0].source == "spse"
    assert results[0].source_url.endswith("/123/pengumumanlelang")
    assert results[0].matched_keyword == "software"
    assert "Rp. 100.000.000,00" in results[0].content


@pytest.mark.asyncio
async def test_spse_adapter_paginates_until_match_limit(monkeypatch):
    html = "authenticityToken = 'token'"
    requests = []
    def handler(request):
        if request.method == "GET":
            return httpx.Response(200, text=html)
        requests.append(request)
        start = int(request.url.params.get("start", "0"))
        if start == 0:
            rows = [[str(i), f"Paket umum {i}", "", "", "", "", "", "", ""] for i in range(100)]
        else:
            rows = [["101", "Pengadaan Software", "Instansi", "Berlangsung", "", "", "", "", "TA"]]
        return httpx.Response(200, json={"data": rows})
    original = httpx.AsyncClient
    monkeypatch.setattr(spse_source.httpx, "AsyncClient", lambda **kwargs: original(transport=httpx.MockTransport(handler)))

    results = await SPSESourceAdapter().search(["software"], limit=1)

    assert len(results) == 1
    assert results[0].source_url.endswith("/101/pengumumanlelang")
    assert len(requests) == 2


@pytest.mark.asyncio
async def test_spse_adapter_raises_on_source_error(monkeypatch):
    original = httpx.AsyncClient
    monkeypatch.setattr(
        spse_source.httpx,
        "AsyncClient",
        lambda **kwargs: original(transport=httpx.MockTransport(lambda request: httpx.Response(503))),
    )
    with pytest.raises(httpx.HTTPStatusError):
        await SPSESourceAdapter().search(["software"])


def test_spse_live_search_persists_for_marketing_and_releases_to_sales(tmp_path, monkeypatch):
    repository = LeadRepository(tmp_path / "spse-leads.db")
    monkeypatch.setattr(leads, "lead_repository", repository)
    monkeypatch.setattr("app.services.spse_service.lead_repository", repository)
    async def no_sheet_write(*args, **kwargs):
        return True
    monkeypatch.setattr(leads.sheets_service, "append_lead", no_sheet_write)
    monkeypatch.setattr(auth, "DB_PATH", tmp_path / "spse-sessions.db")
    monkeypatch.setattr(auth.settings, "app_env", "development")

    marketing, sales = TestClient(app), TestClient(app)
    assert marketing.post("/api/v1/auth/login", json={"role": "marketing"}).status_code == 200
    assert sales.post("/api/v1/auth/login", json={"role": "sales"}).status_code == 200

    result = marketing.post(
        "/api/v1/spse/search",
        json={"keywords": ["software"], "limit": 10},
    )
    assert result.status_code == 200, result.text
    assert result.json()["matched"] >= 1

    pending = marketing.get("/api/v1/leads?source=spse&status=pending").json()
    assert pending
    tender = pending[0]
    assert "spse.inaproc.id" in tender["source_url"]
    assert sales.get(f"/api/v1/leads/{tender['lead_id']}").status_code == 404

    approved = marketing.patch(
        f"/api/v1/leads/{tender['lead_id']}/status",
        json={"marketing_status": "valid"},
    )
    assert approved.status_code == 200
    assert any(x["lead_id"] == tender["lead_id"] for x in sales.get("/api/v1/leads?source=spse").json())

    marketing.close()
    sales.close()