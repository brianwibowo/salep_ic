"""Public SPSE Nasional listing source adapter (homepage listings only)."""

from __future__ import annotations

from datetime import date
from html.parser import HTMLParser
import re
from urllib.parse import urljoin

import httpx

from app.agent.schemas import RawLead


SPSE_NATIONAL_URL = "https://spse.inaproc.id/nasional"
SPSE_SEARCH_URL = "https://spse.inaproc.id/nasional/lelang"
SPSE_DATATABLE_URL = "https://spse.inaproc.id/nasional/dt/lelang"


class _TenderParser(HTMLParser):
    """Extract tender rows from the public listing tables, without browser automation."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.rows: list[dict[str, str]] = []
        self._row: dict[str, str] | None = None
        self._cell = False
        self._anchor = False
        self._anchor_href = ""
        self._anchor_text = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = dict(attrs)
        if tag == "tr":
            self._row = {"cells": "", "title": "", "url": ""}
        elif tag in {"td", "th"} and self._row is not None:
            self._cell = True
        elif tag == "a" and self._row is not None:
            self._anchor = True
            self._anchor_href = attrs_dict.get("href") or ""
            self._anchor_text = ""

    def handle_data(self, data: str) -> None:
        if self._row is not None and self._cell:
            self._row["cells"] += f" {data.strip()}"
        if self._anchor:
            self._anchor_text += data

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._anchor:
            text = " ".join(self._anchor_text.split())
            if self._row is not None and "/lelang/" in self._anchor_href and text:
                self._row["title"] = text
                self._row["url"] = urljoin(SPSE_NATIONAL_URL, self._anchor_href)
            self._anchor = False
        elif tag in {"td", "th"}:
            self._cell = False
        elif tag == "tr" and self._row is not None:
            cells = " ".join(self._row["cells"].split())
            if self._row["url"] and self._row["title"]:
                self._row["cells"] = cells
                self.rows.append(self._row)
            self._row = None


class SPSESourceAdapter:
    """Fetch public tenders from the paginated SPSE Nasional search listing."""

    @property
    def source_name(self) -> str:
        return "spse"

    async def search(
        self,
        keywords: list[str],
        start_date: str = "",
        end_date: str = "",
        limit: int = 50,
    ) -> list[RawLead]:
        del start_date, end_date  # SPSE does not expose a reliable publication date here.
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; SALEP public procurement discovery/1.0)",
            "Accept": "application/json, text/javascript, */*; q=0.01",
        }
        async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
            page = await client.get(SPSE_SEARCH_URL, headers=headers)
            page.raise_for_status()
            token_match = re.search(r"authenticityToken\s*[:=]\s*'([^']+)'", page.text)
            if not token_match:
                raise RuntimeError("Token pencarian publik SPSE tidak ditemukan")
            token = token_match.group(1)
            terms = [term.casefold() for term in keywords if term.strip()]
            results: list[RawLead] = []
            seen: set[str] = set()
            start = 0
            page_size = 100
            while len(results) < limit:
                response = await client.post(
                    f"{SPSE_DATATABLE_URL}?tahun={date.today().year}",
                    data={"draw": "1", "start": str(start), "length": str(page_size), "authenticityToken": token},
                    headers={**headers, "X-Requested-With": "XMLHttpRequest", "Referer": SPSE_SEARCH_URL},
                )
                response.raise_for_status()
                payload = response.json()
                rows = payload.get("data", [])
                if not rows:
                    break
                for item in rows:
                    if len(item) < 9:
                        continue
                    package_id, title = str(item[0]), re.sub(r"<[^>]*>", " ", str(item[1]))
                    title = " ".join(title.split())
                    details = " | ".join(" ".join(str(value or "").split()) for value in item[2:9])
                    url = urljoin(SPSE_SEARCH_URL, f"{package_id}/pengumumanlelang")
                    haystack = f"{title} {details}".casefold()
                    matched = next((term for term in terms if term in haystack), None)
                    if not matched or url in seen:
                        continue
                    seen.add(url)
                    results.append(RawLead(source="spse", source_url=url, author_name="SPSE Nasional", content=f"Nama paket: {title}\nInformasi paket: {details}", matched_keyword=matched))
                    if len(results) >= limit:
                        break
                start += len(rows)
                if len(rows) < page_size:
                    break
        return results

    async def health_check(self) -> dict[str, str]:
        return {"status": "ok", "source": SPSE_SEARCH_URL}