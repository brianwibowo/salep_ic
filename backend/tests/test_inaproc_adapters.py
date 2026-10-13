from __future__ import annotations

import asyncio
import json
from pathlib import Path

from app.domain.procurement import ProcurementTrack
from app.sources.inaproc.adapters import InaprocAdapter, parse_detail_fields


class FakeResponse:
    def __init__(self, *, text: str = "", payload: dict | None = None) -> None:
        self.text = text
        self._payload = payload
        self.status_code = 200

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self._payload or {}


class FakeClient:
    def __init__(self) -> None:
        self.posts: list[dict] = []
        self.gets: list[str] = []

    async def get(self, url: str, **kwargs):
        self.gets.append(url)
        if "caripaketctr/search" in url:
            params = kwargs.get("params") or {}
            rows = [[1, "Managed Service", "Rp 100.000.000,00", "Jasa", "Produk Dalam Negeri", "Usaha Kecil", "E-Purchasing", "2026", "Instansi", "Satker", "Jakarta", "62222"]] if int(params.get("start", 0)) == 0 else []
            return FakeResponse(text=json.dumps({"data": rows}), payload={"data": rows, "recordsFiltered": len(rows)})
        if "detailPaket" in url or "/lelang/" in url:
            return FakeResponse(text="""<table><tr><th>Nama Paket</th><td>Managed Service Detail</td></tr><tr><th>Status Kontrak</th><td>Selesai</td></tr><tr><th>Nilai HPS Paket</th><td>Rp 125.000.000,00</td></tr></table>""")
        return FakeResponse(text="<script>var authenticityToken = 'fixture-token';</script>")

    async def post(self, url: str, **kwargs):
        self.posts.append({"url": url, **kwargs})
        start = int((kwargs.get("data") or {}).get("start", 0))
        if "sirup" not in url:
            rows = [["12345", "Tender Server", "Instansi", "Tender Sudah Selesai", "Rp 250.000.000,00"]] if start == 0 else []
        else:
            rows = []
        return FakeResponse(text=json.dumps({"data": rows}), payload={"data": rows, "recordsFiltered": len(rows)})


def test_detail_parser_extracts_status_and_hps() -> None:
    fields = parse_detail_fields("<table><tr><th>Status Kontrak</th><td>Pemutusan Kontrak</td></tr><tr><th>HPS</th><td>Rp 10.000.000</td></tr></table>")
    assert fields["contract_status"] == "Pemutusan Kontrak"
    assert fields["hps_amount"] == "Rp 10.000.000"


def test_sirup_adapter_paginates_and_enriches_detail() -> None:
    client = FakeClient()
    adapter = InaprocAdapter(client=client, page_size=1)
    packages = asyncio.run(_collect(adapter.iter_sirup(fiscal_year=2026, limit=10)))
    assert len(packages) == 1
    assert packages[0].package_name == "Managed Service Detail"
    assert packages[0].hps_amount == 125_000_000
    assert sum("caripaketctr/search" in url for url in client.gets) == 2


def test_spse_adapter_supports_pencatatan_non_tender() -> None:
    client = FakeClient()
    adapter = InaprocAdapter(client=client, page_size=1)
    packages = asyncio.run(_collect(adapter.iter_spse(track=ProcurementTrack.PENCATATAN_NON_TENDER, fiscal_year=2026, limit=1)))
    assert packages[0].track is ProcurementTrack.PENCATATAN_NON_TENDER
    assert packages[0].current_stage_code == "tender_completed"


async def _collect(iterator):
    results = []
    async for value in iterator:
        results.append(value)
    return results
