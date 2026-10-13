"""HTTP adapters for the public Si-RUP and SPSE Inaproc portals.

The adapters deliberately keep transport, pagination and parsing separate.  A
captured DataTables response can therefore be replayed in contract tests, while
the production job uses the same code with an ordinary HTTP client.  No browser
fingerprint tricks are required: requests are rate limited, session based and
respect the public portal's own pagination contract.
"""

from __future__ import annotations

import hashlib
import asyncio
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from html.parser import HTMLParser
from typing import Any, AsyncIterator, Protocol
from urllib.parse import urljoin, urlparse

import httpx

from app.domain.procurement import ProcurementPackage, ProcurementTrack
from app.sources.inaproc.parsers import (
    clean_text,
    normalize_stage_code,
    parse_amount,
    parse_sirup_rows,
    parse_spse_rows,
)


SPSE_BASE_URL = "https://spse.inaproc.id"
SIRUP_BASE_URL = "https://sirup.inaproc.id"


@dataclass(frozen=True)
class TrackConfig:
    track: ProcurementTrack
    listing_path: str
    datatable_path: str
    detail_path_template: str
    include_year_query: bool = True


SPSE_TRACKS: dict[ProcurementTrack, TrackConfig] = {
    ProcurementTrack.TENDER: TrackConfig(
        ProcurementTrack.TENDER, "/nasional/lelang", "/nasional/dt/lelang", "/nasional/lelang/{id}/pengumumanlelang"
    ),
    ProcurementTrack.NON_TENDER: TrackConfig(
        ProcurementTrack.NON_TENDER, "/nasional/nontender", "/nasional/dt/pl", "/nasional/nontender/{id}/pengumumanpl"
    ),
    ProcurementTrack.PENCATATAN_NON_TENDER: TrackConfig(
        ProcurementTrack.PENCATATAN_NON_TENDER, "/nasional/pencatatan", "/nasional/dt/nonspk", "/nasional/pencatatan/pengumumannonspk?id={id}"
    ),
    ProcurementTrack.SWAKELOLA: TrackConfig(
        ProcurementTrack.SWAKELOLA, "/nasional/swakelola", "/nasional/dt/swakelola", "/nasional/swakelola/{id}/pengumuman", False
    ),
    ProcurementTrack.DARURAT: TrackConfig(
        ProcurementTrack.DARURAT, "/nasional/darurat", "/nasional/dt/darurat-list", "/nasional/darurat/pengumumandarurat?id={id}", False
    ),
}


class AsyncTransport(Protocol):
    async def get(self, url: str, **kwargs: Any) -> Any: ...

    async def post(self, url: str, **kwargs: Any) -> Any: ...


class _DetailParser(HTMLParser):
    """Read label/value pairs from both table and definition-list markup."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.rows: list[list[str]] = []
        self._cells: list[str] = []
        self._cell_text = ""
        self._in_cell = False
        self._in_row = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "tr":
            self._in_row = True
            self._cells = []
        elif tag in {"td", "th", "dt", "dd"}:
            self._in_cell = True
            self._cell_text = ""

    def handle_data(self, data: str) -> None:
        if self._in_cell:
            self._cell_text += f" {data}"

    def handle_endtag(self, tag: str) -> None:
        if tag in {"td", "th", "dt", "dd"} and self._in_cell:
            text = clean_text(self._cell_text)
            if text:
                self._cells.append(text)
            self._in_cell = False
        if tag == "tr" and self._in_row:
            if self._cells:
                self.rows.append(self._cells)
            self._in_row = False


def parse_detail_fields(html: str) -> dict[str, str]:
    parser = _DetailParser()
    parser.feed(html)
    values: dict[str, str] = {}
    for cells in parser.rows:
        if len(cells) < 2:
            continue
        # Most Inaproc detail pages have either Label | Value or a label in
        # the first column followed by several value columns.
        label = cells[0].casefold().rstrip(":")
        value = cells[1]
        if label and value:
            values[label] = value
    text = clean_text(re.sub(r"<[^>]*>", " ", html))
    aliases = {
        "nama paket": "package_name",
        "pagu": "budget_amount",
        "nilai pagu paket": "budget_amount",
        "hps": "hps_amount",
        "nilai hps paket": "hps_amount",
        "instansi": "organization",
        "k/l/pd": "organization",
        "satuan kerja": "satker",
        "lokasi pekerjaan": "location",
        "jenis pengadaan": "procurement_type",
        "metode pemilihan": "procurement_method",
        "tahap tender saat ini": "current_stage_label",
        "status kontrak": "contract_status",
        "jenis kontrak": "contract_type",
    }
    for label, key in aliases.items():
        if key in values:
            continue
        match = re.search(rf"{re.escape(label)}\s*[:\-]\s*([^|]+?)(?=\s+(?:nama paket|pagu|hps|instansi|satuan kerja|lokasi pekerjaan|jenis pengadaan|metode pemilihan|tahap tender saat ini|status kontrak)\s*[:\-]|$)", text, re.I)
        if match:
            values[key] = clean_text(match.group(1))
    return {aliases.get(key, key): value for key, value in values.items()}


def merge_detail(package: ProcurementPackage, html: str) -> ProcurementPackage:
    fields = parse_detail_fields(html)
    updates: dict[str, Any] = {}
    for key in ("package_name", "organization", "satker", "location", "procurement_type", "procurement_method", "contract_type", "current_stage_label", "contract_status"):
        if fields.get(key):
            updates[key] = fields[key]
    for key in ("budget_amount", "hps_amount"):
        if fields.get(key):
            updates[key] = parse_amount(fields[key])
    if updates.get("current_stage_label"):
        updates["current_stage_code"] = normalize_stage_code(updates["current_stage_label"])
    return package.model_copy(update=updates)


def _token(html: str) -> str:
    patterns = (
        r"authenticityToken\s*[:=]\s*['\"]([^'\"]+)",
        r"csrf[_-]?token\s*[:=]\s*['\"]([^'\"]+)",
    )
    for pattern in patterns:
        match = re.search(pattern, html, re.I)
        if match:
            return match.group(1)
    return ""


def _snapshot_id(source: str, url: str, payload: str) -> str:
    digest = hashlib.sha256(f"{source}|{url}|{payload}".encode()).hexdigest()
    return f"{source}_{digest[:24]}"


def _allowed_portal_url(url: str, expected_host: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme == "https" and (parsed.hostname or "").casefold().rstrip(".") == expected_host


class InaprocAdapter:
    """Shared paginated client for Si-RUP and all five public SPSE tracks."""

    def __init__(self, *, client: AsyncTransport | None = None, timeout: float = 30.0, page_size: int = 100, rate_limit_seconds: float = 0.25, max_retries: int = 3) -> None:
        self._client = client
        self.timeout = timeout
        self.page_size = max(1, min(page_size, 500))
        self.rate_limit_seconds = max(0.0, rate_limit_seconds)
        self.max_retries = max(0, max_retries)

    async def _client_context(self):
        if self._client is not None:
            return _NullContext(self._client)
        return httpx.AsyncClient(timeout=self.timeout, follow_redirects=True)

    async def iter_sirup(
        self, *, fiscal_year: int, keyword: str = "", limit: int = 500, fetch_details: bool = True
    ) -> AsyncIterator[ProcurementPackage]:
        async with await self._client_context() as client:
            listing_url = urljoin(SIRUP_BASE_URL, "/sirup/caripaketctr/index")
            page = await self._request(client, "get", listing_url, headers=self._headers(listing_url))
            page.raise_for_status()
            start = 0
            seen: set[str] = set()
            yielded = 0
            while yielded < limit:
                endpoint = urljoin(SIRUP_BASE_URL, "/sirup/caripaketctr/search")
                response = await self._request(
                    client, "get", endpoint,
                    params={"tahunAnggaran": str(fiscal_year), "start": str(start), "length": str(self.page_size), "search[value]": keyword},
                    headers=self._headers(listing_url, ajax=True),
                )
                response.raise_for_status()
                payload = response.json()
                rows = parse_sirup_rows(payload, fiscal_year=fiscal_year, base_url=SIRUP_BASE_URL + "/")
                if not rows:
                    break
                page_new_ids = {package.external_id for package in rows if package.external_id not in seen}
                # Protect the worker when an upstream proxy ignores the
                # offset and repeats the same full page forever.
                if start and not page_new_ids:
                    break
                for package in rows:
                    if package.external_id in seen:
                        continue
                    seen.add(package.external_id)
                    if keyword and keyword.casefold() not in package.package_name.casefold():
                        continue
                    if fetch_details:
                        package = await self._fetch_package_detail(client, package)
                    package = package.model_copy(update={"raw_snapshot_id": _snapshot_id("sirup", endpoint, response.text)})
                    yield package
                    yielded += 1
                    if yielded >= limit:
                        break
                start += len(payload.get("data", [])) or self.page_size
                if len(payload.get("data", [])) < self.page_size:
                    break

    async def iter_spse(
        self, *, track: ProcurementTrack, fiscal_year: int, keyword: str = "", limit: int = 500, fetch_details: bool = True
    ) -> AsyncIterator[ProcurementPackage]:
        if track not in SPSE_TRACKS:
            raise ValueError(f"Track SPSE tidak didukung: {track}")
        config = SPSE_TRACKS[track]
        async with await self._client_context() as client:
            listing_url = urljoin(SPSE_BASE_URL, config.listing_path)
            page = await self._request(client, "get", listing_url, headers=self._headers(listing_url))
            page.raise_for_status()
            token = _token(page.text)
            start = 0
            seen: set[str] = set()
            yielded = 0
            while yielded < limit:
                endpoint = urljoin(SPSE_BASE_URL, config.datatable_path)
                request_params = {
                    **({"tahun": str(fiscal_year)} if config.include_year_query else {}),
                    "start": str(start),
                    "length": str(self.page_size),
                }
                response = await self._request(
                    client, "post", endpoint,
                    params=request_params,
                    data={"draw": "1", "start": str(start), "length": str(self.page_size), "authenticityToken": token},
                    headers=self._headers(listing_url, ajax=True),
                )
                response.raise_for_status()
                payload = response.json()
                rows = parse_spse_rows(payload, track=track, fiscal_year=fiscal_year, base_url=SPSE_BASE_URL + "/nasional/")
                if not rows:
                    break
                page_new_ids = {package.external_id for package in rows if package.external_id not in seen}
                if start and not page_new_ids:
                    break
                for package in rows:
                    haystack = " ".join(filter(None, (package.package_name, package.organization, package.current_stage_label))).casefold()
                    if package.external_id in seen:
                        continue
                    seen.add(package.external_id)
                    if keyword and keyword.casefold() not in haystack:
                        continue
                    if track != ProcurementTrack.TENDER:
                        package = package.model_copy(update={"source_url": urljoin(SPSE_BASE_URL, config.detail_path_template.format(id=package.external_id))})
                    if fetch_details:
                        package = await self._fetch_package_detail(client, package)
                    package = package.model_copy(update={"raw_snapshot_id": _snapshot_id("spse", endpoint, response.text)})
                    yield package
                    yielded += 1
                    if yielded >= limit:
                        break
                start += len(payload.get("data", [])) or self.page_size
                if len(payload.get("data", [])) < self.page_size:
                    break

    async def _fetch_package_detail(self, client: AsyncTransport, package: ProcurementPackage) -> ProcurementPackage:
        expected_host = SIRUP_BASE_URL.split("//", 1)[1] if package.source == "sirup" else SPSE_BASE_URL.split("//", 1)[1]
        if not _allowed_portal_url(package.source_url, expected_host):
            return package
        try:
            response = await self._request(client, "get", package.source_url, headers=self._headers(package.source_url))
            response.raise_for_status()
            return merge_detail(package, response.text)
        except Exception:
            # Listing data remains valid if a detail page is temporarily
            # blocked; the source document is still persisted for retry.
            return package

    async def _request(self, client: AsyncTransport, method: str, url: str, **kwargs: Any) -> Any:
        """Respectful retry policy for public endpoints (429/5xx only)."""
        for attempt in range(self.max_retries + 1):
            if self.rate_limit_seconds and attempt == 0:
                await asyncio.sleep(self.rate_limit_seconds)
            response = await getattr(client, method)(url, **kwargs)
            status = getattr(response, "status_code", 200)
            if status not in {429, 500, 502, 503, 504} or attempt >= self.max_retries:
                return response
            retry_after = getattr(response, "headers", {}).get("Retry-After")
            try:
                delay = float(retry_after) if retry_after else 2 ** attempt
            except (TypeError, ValueError):
                delay = 2 ** attempt
            await asyncio.sleep(min(delay, 30.0))
        raise RuntimeError("HTTP retry loop exhausted")

    @staticmethod
    def _headers(referer: str, *, ajax: bool = False) -> dict[str, str]:
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; SALEP Inaproc adapter/2.0)",
            "Accept": "application/json, text/javascript, text/html;q=0.9, */*;q=0.8",
            "Referer": referer,
        }
        if ajax:
            headers["X-Requested-With"] = "XMLHttpRequest"
        return headers


class _NullContext:
    def __init__(self, value: AsyncTransport) -> None:
        self.value = value

    async def __aenter__(self) -> AsyncTransport:
        return self.value

    async def __aexit__(self, *args: Any) -> None:
        return None


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
